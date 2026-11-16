"""The upload body a stake POSTs to /api/readings (spec 8.1).

This model checks shape and types only: required fields, types, and the allowed values of
time_status, trigger and delivery. A body that fails it is a 422 (task card B3). The value
ranges in spec 8.3 are checked later, item by item, in app.ingest.

Field names are the frozen contract (spec 8, 3.1): never rename, remove or retype one.
Unknown fields are refused, so a renamed field fails loudly instead of being stored as null.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TimeStatus = Literal["synced", "estimated", "unknown"]


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UploadReading(_Contract):
    reading_id: str
    boot_id: int
    uptime_s: int
    device_time: datetime | None
    time_status: TimeStatus
    moisture_raw: int
    moisture_pct: float | None
    lux: int | None
    battery_mv: int
    reservoir_low: bool
    sensor_fault: bool
    soil_temp_c: float | None


class UploadEvent(_Contract):
    event_id: str
    boot_id: int
    uptime_s: int
    device_time: datetime | None
    time_status: TimeStatus
    duration_ms: int
    trigger: Literal["auto", "manual", "test"]
    request_id: int | None
    moisture_before: float | None
    delivery: Literal["ok", "failed", "unchecked", "refused"]


class ReadingsUpload(_Contract):
    serial: str
    firmware_version: str
    sent_time: datetime | None
    sent_boot_id: int
    sent_uptime_s: int
    dropped_count: int
    readings: list[UploadReading]
    events: list[UploadEvent]
