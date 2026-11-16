"""B2: ingest_batch follows spec 10.1 steps 4 to 10."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.ingest import ingest_batch
from app.models import (
    Account,
    DataGap,
    Device,
    Event,
    Plant,
    Reading,
    RejectLog,
    Species,
    WaterRequest,
)
from app.schemas.upload import ReadingsUpload

RECEIVED = datetime(2026, 12, 8, 19, 31, 30)
SENT = datetime(2026, 12, 8, 19, 31, 4)
SERIAL = "SPROUT-001"


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def stake(db_session):
    db_session.add(Account(id=1, email="dev@sprout.local", password_hash="x"))
    species = Species(
        common_name="Basil",
        scientific_name="Ocimum basilicum",
        days_between_waterings=Decimal("3.0"),
        light_hours=Decimal("6.0"),
        water_threshold_pct=Decimal("35.0"),
        source_url="https://example.edu/basil",
    )
    db_session.add(species)
    db_session.flush()
    plant = Plant(
        account_id=1,
        species_id=species.id,
        name="Basil",
        moisture_threshold=Decimal("35.0"),
        jar_capacity_ml=1000,
    )
    db_session.add(plant)
    db_session.flush()
    device = Device(serial=SERIAL, key_hash="x", account_id=1, plant_id=plant.id)
    db_session.add(device)
    db_session.flush()
    return device


def reading(n, *, uptime_s=86400, t=datetime(2026, 12, 8, 14, 0), status="synced", **over):
    r = {
        "reading_id": f"{SERIAL}-{n:06d}",
        "boot_id": 17,
        "uptime_s": uptime_s,
        "device_time": iso(t) if t else None,
        "time_status": status,
        "moisture_raw": 2025,
        "moisture_pct": 42.5,
        "lux": 8200,
        "battery_mv": 3810,
        "reservoir_low": False,
        "sensor_fault": False,
        "soil_temp_c": None,
    }
    r.update(over)
    return r


def event(n, *, delivery="ok", trigger="auto", request_id=None, duration_ms=8400, **over):
    e = {
        "event_id": f"{SERIAL}-E{n:06d}",
        "boot_id": 17,
        "uptime_s": 69120,
        "device_time": iso(datetime(2026, 12, 8, 9, 12)),
        "time_status": "synced",
        "duration_ms": duration_ms,
        "trigger": trigger,
        "request_id": request_id,
        "moisture_before": 28.1,
        "delivery": delivery,
    }
    e.update(over)
    return e


def upload(readings=(), events=(), **over):
    body = {
        "serial": SERIAL,
        "firmware_version": "1.0.0",
        "sent_time": iso(SENT),
        "sent_boot_id": 17,
        "sent_uptime_s": 106264,
        "dropped_count": 0,
        "readings": list(readings),
        "events": list(events),
    }
    body.update(over)
    return ReadingsUpload.model_validate(body)


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_repeated_reading_id_is_ignored(db_session, stake):
    batch = upload([reading(1), reading(2)])
    first = ingest_batch(db_session, stake, batch, RECEIVED)
    again = ingest_batch(db_session, stake, batch, RECEIVED)
    assert (first.readings_stored, again.readings_stored, again.readings_repeated) == (2, 0, 2)
    assert count(db_session, Reading) == 2


def test_item_outside_its_range_is_logged_and_skipped(db_session, stake):
    result = ingest_batch(
        db_session, stake, upload([reading(1), reading(2, battery_mv=9000)]), RECEIVED
    )
    assert (result.readings_stored, result.readings_rejected) == (1, 1)
    logged = db_session.scalars(select(RejectLog)).all()
    assert len(logged) == 1
    assert logged[0].serial == SERIAL and "battery_mv" in logged[0].reason


def test_old_or_future_times_are_rejected(db_session, stake):
    too_old = reading(1, t=RECEIVED - timedelta(days=91))
    future = reading(2, t=RECEIVED + timedelta(minutes=10))
    result = ingest_batch(db_session, stake, upload([too_old, future]), RECEIVED)
    assert result.readings_rejected == 2


def test_unchecked_event_then_ok_updates_delivery_only(db_session, stake):
    ingest_batch(db_session, stake, upload(events=[event(1, delivery="unchecked")]), RECEIVED)
    later = event(1, delivery="ok", duration_ms=1000)
    result = ingest_batch(db_session, stake, upload(events=[later]), RECEIVED)
    stored = db_session.scalars(select(Event)).all()
    assert result.events_updated == 1 and len(stored) == 1
    assert stored[0].delivery == "ok"
    assert stored[0].duration_ms == 8400  # nothing else changed


def test_redating_current_boot_only(db_session, stake):
    estimated = reading(1, uptime_s=6264, t=datetime(2026, 12, 7, 1, 0), status="estimated")
    unknown = reading(2, uptime_s=7264, t=None, status="unknown")
    old_boot = reading(3, uptime_s=500, t=None, status="unknown", boot_id=16)
    ingest_batch(db_session, stake, upload([estimated, unknown, old_boot]), RECEIVED)
    rows = {r.reading_id[-1]: r for r in db_session.scalars(select(Reading))}
    # device_time = anchor - (sent_uptime_s - uptime_s), anchor = sent_time
    assert rows["1"].device_time == SENT - timedelta(seconds=106264 - 6264)
    assert rows["2"].device_time == SENT - timedelta(seconds=106264 - 7264)
    assert rows["1"].time_status == rows["2"].time_status == "estimated"
    assert rows["3"].device_time is None and rows["3"].time_status == "unknown"


def test_redating_uses_received_at_without_sent_time(db_session, stake):
    unknown = reading(1, uptime_s=6264, t=None, status="unknown")
    ingest_batch(db_session, stake, upload([unknown], sent_time=None), RECEIVED)
    stored = db_session.scalar(select(Reading))
    assert stored.device_time == RECEIVED - timedelta(seconds=106264 - 6264)


def test_dropped_count_writes_a_data_gap(db_session, stake):
    earlier = reading(1, t=datetime(2026, 12, 6, 10, 0))
    ingest_batch(db_session, stake, upload([earlier]), RECEIVED)
    batch = upload(
        [reading(2, t=datetime(2026, 12, 8, 13, 0)), reading(3, t=datetime(2026, 12, 8, 12, 0))],
        dropped_count=4,
    )
    ingest_batch(db_session, stake, batch, RECEIVED)
    gap = db_session.scalar(select(DataGap))
    assert gap.dropped_count == 4
    assert gap.gap_start == datetime(2026, 12, 6, 10, 0)  # latest stored before the batch
    assert gap.gap_end == datetime(2026, 12, 8, 12, 0)  # oldest in the batch


def test_last_seen_and_firmware_version_are_updated(db_session, stake):
    ingest_batch(db_session, stake, upload([reading(1)], firmware_version="1.2.3"), RECEIVED)
    assert stake.last_seen == RECEIVED
    assert stake.firmware_version == "1.2.3"


def test_volume_is_added_to_ml_since_refill_except_refused(db_session, stake):
    stake.ml_per_s = Decimal("7.14")
    events = [event(1, duration_ms=8400), event(2, duration_ms=0, delivery="refused")]
    ingest_batch(db_session, stake, upload(events=events), RECEIVED)
    plant = db_session.get(Plant, stake.plant_id)
    assert plant.ml_since_refill == Decimal("60.0")  # 8.4 s x 7.14 ml/s, refused not added
    volumes = sorted(e.volume_ml for e in db_session.scalars(select(Event)))
    assert volumes == [Decimal("0.0"), Decimal("60.0")]


def test_no_volume_while_flow_rate_unknown(db_session, stake):
    ingest_batch(db_session, stake, upload(events=[event(1)]), RECEIVED)
    assert db_session.scalar(select(Event)).volume_ml is None


@pytest.mark.parametrize(("delivery", "outcome"), [("ok", "delivered"), ("refused", "refused")])
def test_manual_event_resolves_its_water_request(db_session, stake, delivery, outcome):
    request = WaterRequest(plant_id=stake.plant_id, requested_at=SENT - timedelta(days=1))
    db_session.add(request)
    db_session.flush()
    manual = event(1, trigger="manual", request_id=request.id, delivery=delivery)
    ingest_batch(db_session, stake, upload(events=[manual]), RECEIVED)
    assert request.outcome == outcome
    assert request.resolved_at == RECEIVED


def test_items_attach_to_the_stakes_plant(db_session, stake):
    ingest_batch(db_session, stake, upload([reading(1)], [event(1)]), RECEIVED)
    assert db_session.scalar(select(Reading)).plant_id == stake.plant_id
    assert db_session.scalar(select(Event)).plant_id == stake.plant_id
