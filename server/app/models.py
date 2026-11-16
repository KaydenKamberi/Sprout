"""SQLAlchemy models: one per table in spec 9.2, with the spec's exact names and types.

The migration (migrations/versions/0001_initial_schema.py) creates the tables from the
spec's SQL; these models mirror that SQL so the rest of the server can use the tables.
Never rename, remove or retype a column here without changing spec section 9 first.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.mysql import (
    BIGINT,
    CHAR,
    DATETIME,
    DECIMAL,
    DOUBLE,
    ENUM,
    INTEGER,
    MEDIUMTEXT,
    TEXT,
    TINYINT,
    VARCHAR,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

ID = BIGINT(unsigned=True)
UINT = INTEGER(unsigned=True)
TIME3 = DATETIME(fsp=3)
NOW3 = text("CURRENT_TIMESTAMP(3)")
TIME_STATUS = ENUM("synced", "estimated", "unknown")


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    timezone: Mapped[str] = mapped_column(
        VARCHAR(64), nullable=False, server_default=text("'America/Los_Angeles'")
    )
    created_at: Mapped[datetime] = mapped_column(TIME3, nullable=False, server_default=NOW3)


class LoginSession(Base):
    """A login session behind the sprout_session cookie (spec 8.6)."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ID, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)


class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(UINT, primary_key=True, autoincrement=True)
    common_name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    scientific_name: Mapped[str] = mapped_column(VARCHAR(150), nullable=False)
    days_between_waterings: Mapped[Decimal] = mapped_column(DECIMAL(4, 1), nullable=False)
    light_hours: Mapped[Decimal] = mapped_column(DECIMAL(3, 1), nullable=False)
    water_threshold_pct: Mapped[Decimal] = mapped_column(DECIMAL(4, 1), nullable=False)
    source_url: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    toxic_to_cats: Mapped[int | None] = mapped_column(TINYINT(1), nullable=True)
    toxic_to_dogs: Mapped[int | None] = mapped_column(TINYINT(1), nullable=True)
    perenual_id: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    image_url: Mapped[str | None] = mapped_column(VARCHAR(500), nullable=True)
    care_text: Mapped[str | None] = mapped_column(TEXT, nullable=True)


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ID, ForeignKey("accounts.id"), nullable=False)
    species_id: Mapped[int] = mapped_column(UINT, ForeignKey("species.id"), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    dry_raw: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    wet_raw: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    moisture_threshold: Mapped[Decimal] = mapped_column(DECIMAL(4, 1), nullable=False)
    target_ml: Mapped[Decimal] = mapped_column(
        DECIMAL(6, 1), nullable=False, server_default=text("60.0")
    )
    jar_capacity_ml: Mapped[int] = mapped_column(INTEGER, nullable=False)
    ml_since_refill: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 1), nullable=False, server_default=text("0")
    )
    effective_interval_h: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 1), nullable=True)
    learning_epoch: Mapped[int] = mapped_column(UINT, nullable=False, server_default=text("1"))
    epoch_started_at: Mapped[datetime] = mapped_column(TIME3, nullable=False, server_default=NOW3)
    epoch_reason: Mapped[str] = mapped_column(
        ENUM("created", "repot", "moved", "soil_change", "other"),
        nullable=False,
        server_default=text("'created'"),
    )
    is_simulated: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(TIME3, nullable=False, server_default=NOW3)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    serial: Mapped[str] = mapped_column(VARCHAR(32), nullable=False, unique=True)
    key_hash: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    claim_code_hash: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    account_id: Mapped[int | None] = mapped_column(ID, ForeignKey("accounts.id"), nullable=True)
    plant_id: Mapped[int | None] = mapped_column(
        ID, ForeignKey("plants.id"), nullable=True, unique=True
    )
    name: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    ml_per_s: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    retired_at: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)


class Calibration(Base):
    __tablename__ = "calibrations"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ID, ForeignKey("plants.id"), nullable=False)
    device_id: Mapped[int | None] = mapped_column(ID, ForeignKey("devices.id"), nullable=True)
    dry_raw: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    wet_raw: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    reason: Mapped[str] = mapped_column(
        ENUM("setup", "recalibration", "repot", "sensor_replaced", "reassigned"), nullable=False
    )
    set_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)


class WaterRequest(Base):
    __tablename__ = "water_requests"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ID, ForeignKey("plants.id"), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    outcome: Mapped[str] = mapped_column(
        ENUM("pending", "delivered", "refused", "expired"),
        nullable=False,
        server_default=text("'pending'"),
    )


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        Index("idx_readings_plant_time", "plant_id", "device_time"),
        Index("idx_readings_device_received", "device_id", "received_at"),
    )

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int | None] = mapped_column(ID, ForeignKey("plants.id"), nullable=True)
    device_id: Mapped[int] = mapped_column(ID, ForeignKey("devices.id"), nullable=False)
    reading_id: Mapped[str] = mapped_column(VARCHAR(40), nullable=False, unique=True)
    boot_id: Mapped[int] = mapped_column(UINT, nullable=False)
    uptime_s: Mapped[int] = mapped_column(UINT, nullable=False)
    device_time: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    time_status: Mapped[str] = mapped_column(TIME_STATUS, nullable=False)
    received_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    moisture_raw: Mapped[int] = mapped_column(INTEGER, nullable=False)
    moisture_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1), nullable=True)
    sensor_fault: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("0"))
    lux: Mapped[int | None] = mapped_column(UINT, nullable=True)
    battery_mv: Mapped[int] = mapped_column(INTEGER, nullable=False)
    reservoir_low: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    soil_temp_c: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1), nullable=True)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (Index("idx_events_plant_time", "plant_id", "device_time"),)

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int | None] = mapped_column(ID, ForeignKey("plants.id"), nullable=True)
    device_id: Mapped[int] = mapped_column(ID, ForeignKey("devices.id"), nullable=False)
    event_id: Mapped[str] = mapped_column(VARCHAR(40), nullable=False, unique=True)
    boot_id: Mapped[int] = mapped_column(UINT, nullable=False)
    uptime_s: Mapped[int] = mapped_column(UINT, nullable=False)
    device_time: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    time_status: Mapped[str] = mapped_column(TIME_STATUS, nullable=False)
    received_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    duration_ms: Mapped[int] = mapped_column(UINT, nullable=False)
    volume_ml: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 1), nullable=True)
    trigger_type: Mapped[str] = mapped_column(ENUM("auto", "manual", "test"), nullable=False)
    request_id: Mapped[int | None] = mapped_column(
        ID, ForeignKey("water_requests.id"), nullable=True
    )
    moisture_before: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1), nullable=True)
    delivery: Mapped[str] = mapped_column(
        ENUM("ok", "failed", "unchecked", "refused"), nullable=False
    )


class DataGap(Base):
    __tablename__ = "data_gaps"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ID, ForeignKey("devices.id"), nullable=False)
    plant_id: Mapped[int | None] = mapped_column(ID, ForeignKey("plants.id"), nullable=True)
    received_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    dropped_count: Mapped[int] = mapped_column(UINT, nullable=False)
    gap_start: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    gap_end: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)


class Cycle(Base):
    __tablename__ = "cycles"
    __table_args__ = (UniqueConstraint("plant_id", "start_event_id", name="uq_cycle"),)

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ID, ForeignKey("plants.id"), nullable=False)
    epoch: Mapped[int] = mapped_column(UINT, nullable=False)
    start_event_id: Mapped[int] = mapped_column(ID, nullable=False)
    end_event_id: Mapped[int] = mapped_column(ID, nullable=False)
    start_time: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    end_time: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    start_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1), nullable=True)
    end_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1), nullable=True)
    hours: Mapped[Decimal] = mapped_column(DECIMAL(7, 2), nullable=False)
    hours_to_threshold: Mapped[Decimal | None] = mapped_column(DECIMAL(7, 2), nullable=True)
    rate_pct_per_hour: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 3), nullable=True)
    mean_daily_lux: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    valid: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    exclusion_reason: Mapped[str | None] = mapped_column(
        ENUM(
            "manual_or_test_watering",
            "failed_or_refused_event",
            "sensor_fault",
            "reading_gap",
            "data_gap_reported",
            "unknown_time",
            "too_few_readings",
            "non_positive_rate",
            "calibration_changed",
            "other",
        ),
        nullable=True,
    )
    computed_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)


class ModelFit(Base):
    __tablename__ = "model_fits"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ID, ForeignKey("plants.id"), nullable=False)
    epoch: Mapped[int] = mapped_column(UINT, nullable=False)
    fitted_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    model_type: Mapped[str] = mapped_column(ENUM("mean_interval", "regression"), nullable=False)
    model_version: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    in_use: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("0"))
    learned_interval_h: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)
    intercept: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)
    light_coef: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)
    temp_coef: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)
    r2: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)
    cycle_count: Mapped[int] = mapped_column(UINT, nullable=False)
    mae_learned_h: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)
    mae_species_h: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)
    mae_mean_h: Mapped[float | None] = mapped_column(DOUBLE, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ID, ForeignKey("plants.id"), nullable=False)
    type: Mapped[str] = mapped_column(
        ENUM(
            "low_water",
            "low_battery",
            "low_light",
            "device_offline",
            "failed_delivery",
            "pump_shortfall",
        ),
        nullable=False,
    )
    raised_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    cleared_at: Mapped[datetime | None] = mapped_column(TIME3, nullable=True)
    dismissed: Mapped[int] = mapped_column(TINYINT(1), nullable=False, server_default=text("0"))


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ID, ForeignKey("plants.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    photo_path: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(VARCHAR(500), nullable=True)
    condition: Mapped[str] = mapped_column(
        ENUM(
            "healthy",
            "underwatered",
            "overwatered_or_root_rot",
            "nutrient_deficiency",
            "too_much_light",
            "too_little_light",
            "pests",
            "fungal_or_leaf_spot",
            "not_a_plant",
            "unclear",
        ),
        nullable=False,
    )
    observation: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    check_yourself: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    search_term: Mapped[str | None] = mapped_column(VARCHAR(200), nullable=True)
    advice: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    provider: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    raw_response: Mapped[str | None] = mapped_column(MEDIUMTEXT, nullable=True)
    flagged_for_review: Mapped[int] = mapped_column(
        TINYINT(1), nullable=False, server_default=text("0")
    )


class RejectLog(Base):
    __tablename__ = "reject_log"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    serial: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    received_at: Mapped[datetime] = mapped_column(TIME3, nullable=False)
    reason: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    payload_excerpt: Mapped[str | None] = mapped_column(VARCHAR(500), nullable=True)
