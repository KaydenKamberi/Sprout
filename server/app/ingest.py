"""ingest_batch: the shared core of POST /api/readings (spec 10.1, steps 4 to 10).

The endpoint (task card B3) checks the stake and validates the body, then calls this inside
one transaction and commits. The simulator (task card B2) calls it the same way, so simulated
data takes exactly the path real data does.

This function writes inside the caller's transaction and never commits.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DataGap, Device, Event, Plant, Reading, RejectLog, WaterRequest
from app.schemas.upload import ReadingsUpload, UploadEvent, UploadReading

# Spec 8.3 ranges and 16.2 "Timestamp rejection" (future with 5 min slack, or older than
# 90 days). Times are compared with received_at, the moment this batch reached the server.
FUTURE_SLACK = timedelta(minutes=5)
MAX_AGE = timedelta(days=90)


@dataclass
class IngestResult:
    readings_stored: int = 0
    readings_repeated: int = 0
    readings_rejected: int = 0
    events_stored: int = 0
    events_repeated: int = 0
    events_updated: int = 0
    events_rejected: int = 0
    rejections: list[str] = field(default_factory=list)


def to_utc_naive(t: datetime | None) -> datetime | None:
    """Times are stored as UTC DATETIME(3) without a zone (spec 9, 8.8)."""
    if t is None:
        return None
    if t.tzinfo is not None:
        t = t.astimezone(UTC).replace(tzinfo=None)
    return t


def _time_problem(t: datetime | None, received_at: datetime) -> str | None:
    if t is None:
        return None
    if t > received_at + FUTURE_SLACK:
        return "device_time is in the future"
    if t < received_at - MAX_AGE:
        return "device_time is older than 90 days"
    return None


def _reading_problem(r: UploadReading, serial: str, received_at: datetime) -> str | None:
    if not re.fullmatch(rf"{re.escape(serial)}-\d{{6}}", r.reading_id):
        return "reading_id does not match the 8.1 format"
    if r.boot_id < 0 or r.uptime_s < 0:
        return "boot_id and uptime_s must be 0 or more"
    if problem := _time_problem(to_utc_naive(r.device_time), received_at):
        return problem
    if not 0 <= r.moisture_raw <= 4095:
        return "moisture_raw outside 0 to 4095"
    if r.moisture_pct is not None and not 0 <= r.moisture_pct <= 100:
        return "moisture_pct outside 0 to 100"
    if r.lux is not None and not 0 <= r.lux <= 120_000:
        return "lux outside 0 to 120,000"
    if not 2500 <= r.battery_mv <= 4500:
        return "battery_mv outside 2,500 to 4,500"
    if r.soil_temp_c is not None:
        return "soil_temp_c must be null in v1"
    return None


def _event_problem(
    session: Session, e: UploadEvent, serial: str, device: Device, received_at: datetime
) -> str | None:
    if not re.fullmatch(rf"{re.escape(serial)}-E\d{{6}}", e.event_id):
        return "event_id does not match the 8.1 format"
    if e.boot_id < 0 or e.uptime_s < 0:
        return "boot_id and uptime_s must be 0 or more"
    if problem := _time_problem(to_utc_naive(e.device_time), received_at):
        return problem
    if not 0 <= e.duration_ms <= 15_000:
        return "duration_ms outside 0 to 15,000"
    if e.moisture_before is not None and not 0 <= e.moisture_before <= 100:
        return "moisture_before outside 0 to 100"
    if e.request_id is not None:
        request = session.get(WaterRequest, e.request_id)
        if request is None or request.plant_id != device.plant_id:
            return "request_id is not a water request for this stake's plant"
    return None


def _reject(session: Session, serial: str, received_at: datetime, reason: str, item) -> None:
    excerpt = json.dumps(item.model_dump(mode="json"))[:500]
    session.add(
        RejectLog(serial=serial, received_at=received_at, reason=reason, payload_excerpt=excerpt)
    )


def _redate(item, upload: ReadingsUpload, anchor: datetime) -> tuple[datetime | None, str]:
    """10.1 step 6: re-date current-boot items whose time is unknown or estimated."""
    device_time = to_utc_naive(item.device_time)
    if item.boot_id == upload.sent_boot_id and item.time_status in ("unknown", "estimated"):
        return anchor - timedelta(seconds=upload.sent_uptime_s - item.uptime_s), "estimated"
    return device_time, item.time_status


def ingest_batch(
    session: Session, device: Device, upload: ReadingsUpload, received_at: datetime
) -> IngestResult:
    received_at = to_utc_naive(received_at)
    serial = device.serial
    result = IngestResult()
    anchor = to_utc_naive(upload.sent_time) or received_at
    plant = session.get(Plant, device.plant_id) if device.plant_id is not None else None
    latest_before = session.scalar(
        select(func.max(Reading.device_time)).where(Reading.device_id == device.id)
    )
    batch_times: list[datetime] = []

    # Step 4: readings.
    seen_ids = set(
        session.scalars(
            select(Reading.reading_id).where(
                Reading.reading_id.in_([r.reading_id for r in upload.readings])
            )
        )
    )
    for r in upload.readings:
        if problem := _reading_problem(r, serial, received_at):
            _reject(session, serial, received_at, problem, r)
            result.readings_rejected += 1
            result.rejections.append(f"{r.reading_id}: {problem}")
            continue
        if r.reading_id in seen_ids:
            result.readings_repeated += 1
            continue
        seen_ids.add(r.reading_id)
        device_time, time_status = _redate(r, upload, anchor)
        if device_time is not None:
            batch_times.append(device_time)
        session.add(
            Reading(
                plant_id=device.plant_id,
                device_id=device.id,
                reading_id=r.reading_id,
                boot_id=r.boot_id,
                uptime_s=r.uptime_s,
                device_time=device_time,
                time_status=time_status,
                received_at=received_at,
                moisture_raw=r.moisture_raw,
                moisture_pct=r.moisture_pct,
                sensor_fault=int(r.sensor_fault),
                lux=r.lux,
                battery_mv=r.battery_mv,
                reservoir_low=int(r.reservoir_low),
                soil_temp_c=None,
            )
        )
        result.readings_stored += 1

    # Step 5: events.
    ml_added = Decimal("0")
    for e in upload.events:
        if problem := _event_problem(session, e, serial, device, received_at):
            _reject(session, serial, received_at, problem, e)
            result.events_rejected += 1
            result.rejections.append(f"{e.event_id}: {problem}")
            continue
        existing = session.scalar(select(Event).where(Event.event_id == e.event_id))
        if existing is not None:
            if existing.delivery == "unchecked" and e.delivery in ("ok", "failed"):
                existing.delivery = e.delivery
                result.events_updated += 1
            else:
                result.events_repeated += 1
            continue
        volume = None
        if device.ml_per_s is not None:
            volume = (Decimal(e.duration_ms) / 1000 * device.ml_per_s).quantize(Decimal("0.1"))
        device_time, time_status = _redate(e, upload, anchor)
        if device_time is not None:
            batch_times.append(device_time)
        session.add(
            Event(
                plant_id=device.plant_id,
                device_id=device.id,
                event_id=e.event_id,
                boot_id=e.boot_id,
                uptime_s=e.uptime_s,
                device_time=device_time,
                time_status=time_status,
                received_at=received_at,
                duration_ms=e.duration_ms,
                volume_ml=volume,
                trigger_type=e.trigger,
                request_id=e.request_id,
                moisture_before=e.moisture_before,
                delivery=e.delivery,
            )
        )
        result.events_stored += 1
        # Step 9: add each new, non-refused event's volume to ml_since_refill.
        if volume is not None and e.delivery != "refused":
            ml_added += volume
        # Step 10: a new manual event answers its water request.
        if e.trigger == "manual" and e.request_id is not None:
            request = session.get(WaterRequest, e.request_id)
            request.outcome = "refused" if e.delivery == "refused" else "delivered"
            request.resolved_at = received_at

    # Step 7: a reported buffer overflow becomes a labelled gap.
    if upload.dropped_count > 0:
        session.add(
            DataGap(
                device_id=device.id,
                plant_id=device.plant_id,
                received_at=received_at,
                dropped_count=upload.dropped_count,
                gap_start=latest_before,
                gap_end=min(batch_times) if batch_times else None,
            )
        )

    # Step 8: the stake was seen.
    device.last_seen = received_at
    device.firmware_version = upload.firmware_version

    if plant is not None and ml_added:
        plant.ml_since_refill = (plant.ml_since_refill or Decimal("0")) + ml_added

    session.flush()
    return result
