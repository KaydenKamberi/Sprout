"""B2 addition: SIM-001's last 14 days exported in the spec 13.2 response shapes."""

import json
from datetime import datetime, timedelta

import pytest

from app.db import get_session
from app.seed import ensure_seed_account, load_species
from app.sim_export import export_plant, write_mock_files
from app.simulator import generate, run
from tests.conftest import empty_all_tables

READING_KEYS = {"t", "moisture_pct", "lux", "battery_mv", "time_status"}
EVENT_KEYS = {"t", "trigger", "duration_ms", "volume_ml", "delivery", "moisture_before"}


def parse(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    session = get_session()
    mp = pytest.MonkeyPatch()
    mp.setenv("SEED_ACCOUNT_PASSWORD", "throwaway-test-password")
    try:
        ensure_seed_account(session)
        load_species(session)
        session.commit()
        run(session, generate(42, datetime(2026, 11, 16)))
        readings, events = export_plant(session, "SIM-001")
        out = tmp_path_factory.mktemp("mock")
        paths = write_mock_files(readings, events, out)
        yield readings, events, paths
    finally:
        mp.undo()
        session.close()
        empty_all_tables()


def test_readings_file_matches_13_2_shape(exported):
    readings, _, (readings_path, _) = exported
    assert set(readings) == {"plant_id", "readings", "gaps"}
    assert readings["readings"], "should hold readings"
    for r in readings["readings"]:
        assert set(r) == READING_KEYS
        assert r["t"].endswith("Z")
        assert r["time_status"] in ("synced", "estimated")  # unknown times are left out
    for g in readings["gaps"]:
        assert set(g) == {"start", "end", "reason"}
    assert json.loads(readings_path.read_text()) == readings


def test_events_file_matches_13_2_shape(exported):
    _, events, (_, events_path) = exported
    assert set(events) == {"plant_id", "events"}
    assert events["events"], "should hold waterings"
    for e in events["events"]:
        assert set(e) == EVENT_KEYS
        assert e["trigger"] in ("auto", "manual", "test")
    assert json.loads(events_path.read_text()) == events


def test_covers_the_last_14_days_in_time_order(exported):
    readings, events, _ = exported
    times = [parse(r["t"]) for r in readings["readings"]]
    assert times == sorted(times)
    assert times[-1] - times[0] <= timedelta(days=14)
    assert times[-1] - times[0] > timedelta(days=12)
    for e in events["events"]:
        assert times[-1] - timedelta(days=14) < parse(e["t"]) <= times[-1] + timedelta(hours=1)
