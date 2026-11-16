"""B1: the migration creates every table in spec 9.2 exactly as the spec writes it."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text

from app.db import get_engine
from app.models import Base
from tests.conftest import alembic_config, app_tables

# Every column of every table in spec 9.2, in order: (name, MySQL column type, nullable).
EXPECTED_COLUMNS = {
    "accounts": [
        ("id", "bigint unsigned", "NO"),
        ("email", "varchar(255)", "NO"),
        ("password_hash", "varchar(255)", "NO"),
        ("timezone", "varchar(64)", "NO"),
        ("created_at", "datetime(3)", "NO"),
    ],
    "sessions": [
        ("id", "char(64)", "NO"),
        ("account_id", "bigint unsigned", "NO"),
        ("created_at", "datetime(3)", "NO"),
        ("expires_at", "datetime(3)", "NO"),
    ],
    "species": [
        ("id", "int unsigned", "NO"),
        ("common_name", "varchar(100)", "NO"),
        ("scientific_name", "varchar(150)", "NO"),
        ("days_between_waterings", "decimal(4,1)", "NO"),
        ("light_hours", "decimal(3,1)", "NO"),
        ("water_threshold_pct", "decimal(4,1)", "NO"),
        ("source_url", "varchar(500)", "NO"),
        ("toxic_to_cats", "tinyint(1)", "YES"),
        ("toxic_to_dogs", "tinyint(1)", "YES"),
        ("perenual_id", "int", "YES"),
        ("image_url", "varchar(500)", "YES"),
        ("care_text", "text", "YES"),
    ],
    "plants": [
        ("id", "bigint unsigned", "NO"),
        ("account_id", "bigint unsigned", "NO"),
        ("species_id", "int unsigned", "NO"),
        ("name", "varchar(100)", "NO"),
        ("dry_raw", "int", "YES"),
        ("wet_raw", "int", "YES"),
        ("moisture_threshold", "decimal(4,1)", "NO"),
        ("target_ml", "decimal(6,1)", "NO"),
        ("jar_capacity_ml", "int", "NO"),
        ("ml_since_refill", "decimal(8,1)", "NO"),
        ("effective_interval_h", "decimal(6,1)", "YES"),
        ("learning_epoch", "int unsigned", "NO"),
        ("epoch_started_at", "datetime(3)", "NO"),
        ("epoch_reason", "enum('created','repot','moved','soil_change','other')", "NO"),
        ("is_simulated", "tinyint(1)", "NO"),
        ("created_at", "datetime(3)", "NO"),
    ],
    "devices": [
        ("id", "bigint unsigned", "NO"),
        ("serial", "varchar(32)", "NO"),
        ("key_hash", "varchar(255)", "NO"),
        ("claim_code_hash", "varchar(255)", "YES"),
        ("claimed_at", "datetime(3)", "YES"),
        ("account_id", "bigint unsigned", "YES"),
        ("plant_id", "bigint unsigned", "YES"),
        ("name", "varchar(100)", "YES"),
        ("ml_per_s", "decimal(5,2)", "YES"),
        ("firmware_version", "varchar(32)", "YES"),
        ("last_seen", "datetime(3)", "YES"),
        ("retired_at", "datetime(3)", "YES"),
    ],
    "calibrations": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "NO"),
        ("device_id", "bigint unsigned", "YES"),
        ("dry_raw", "int", "YES"),
        ("wet_raw", "int", "YES"),
        ("reason", "enum('setup','recalibration','repot','sensor_replaced','reassigned')", "NO"),
        ("set_at", "datetime(3)", "NO"),
    ],
    "water_requests": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "NO"),
        ("requested_at", "datetime(3)", "NO"),
        ("sent_at", "datetime(3)", "YES"),
        ("resolved_at", "datetime(3)", "YES"),
        ("outcome", "enum('pending','delivered','refused','expired')", "NO"),
    ],
    "readings": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "YES"),
        ("device_id", "bigint unsigned", "NO"),
        ("reading_id", "varchar(40)", "NO"),
        ("boot_id", "int unsigned", "NO"),
        ("uptime_s", "int unsigned", "NO"),
        ("device_time", "datetime(3)", "YES"),
        ("time_status", "enum('synced','estimated','unknown')", "NO"),
        ("received_at", "datetime(3)", "NO"),
        ("moisture_raw", "int", "NO"),
        ("moisture_pct", "decimal(4,1)", "YES"),
        ("sensor_fault", "tinyint(1)", "NO"),
        ("lux", "int unsigned", "YES"),
        ("battery_mv", "int", "NO"),
        ("reservoir_low", "tinyint(1)", "NO"),
        ("soil_temp_c", "decimal(4,1)", "YES"),
    ],
    "events": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "YES"),
        ("device_id", "bigint unsigned", "NO"),
        ("event_id", "varchar(40)", "NO"),
        ("boot_id", "int unsigned", "NO"),
        ("uptime_s", "int unsigned", "NO"),
        ("device_time", "datetime(3)", "YES"),
        ("time_status", "enum('synced','estimated','unknown')", "NO"),
        ("received_at", "datetime(3)", "NO"),
        ("duration_ms", "int unsigned", "NO"),
        ("volume_ml", "decimal(6,1)", "YES"),
        ("trigger_type", "enum('auto','manual','test')", "NO"),
        ("request_id", "bigint unsigned", "YES"),
        ("moisture_before", "decimal(4,1)", "YES"),
        ("delivery", "enum('ok','failed','unchecked','refused')", "NO"),
    ],
    "data_gaps": [
        ("id", "bigint unsigned", "NO"),
        ("device_id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "YES"),
        ("received_at", "datetime(3)", "NO"),
        ("dropped_count", "int unsigned", "NO"),
        ("gap_start", "datetime(3)", "YES"),
        ("gap_end", "datetime(3)", "YES"),
    ],
    "cycles": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "NO"),
        ("epoch", "int unsigned", "NO"),
        ("start_event_id", "bigint unsigned", "NO"),
        ("end_event_id", "bigint unsigned", "NO"),
        ("start_time", "datetime(3)", "NO"),
        ("end_time", "datetime(3)", "NO"),
        ("start_pct", "decimal(4,1)", "YES"),
        ("end_pct", "decimal(4,1)", "YES"),
        ("hours", "decimal(7,2)", "NO"),
        ("hours_to_threshold", "decimal(7,2)", "YES"),
        ("rate_pct_per_hour", "decimal(6,3)", "YES"),
        ("mean_daily_lux", "int", "YES"),
        ("valid", "tinyint(1)", "NO"),
        (
            "exclusion_reason",
            "enum('manual_or_test_watering','failed_or_refused_event','sensor_fault','reading_gap','data_gap_reported','unknown_time','too_few_readings','non_positive_rate','calibration_changed','other')",
            "YES",
        ),
        ("computed_at", "datetime(3)", "NO"),
    ],
    "model_fits": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "NO"),
        ("epoch", "int unsigned", "NO"),
        ("fitted_at", "datetime(3)", "NO"),
        ("model_type", "enum('mean_interval','regression')", "NO"),
        ("model_version", "varchar(20)", "NO"),
        ("in_use", "tinyint(1)", "NO"),
        ("learned_interval_h", "double", "YES"),
        ("intercept", "double", "YES"),
        ("light_coef", "double", "YES"),
        ("temp_coef", "double", "YES"),
        ("r2", "double", "YES"),
        ("cycle_count", "int unsigned", "NO"),
        ("mae_learned_h", "double", "YES"),
        ("mae_species_h", "double", "YES"),
        ("mae_mean_h", "double", "YES"),
    ],
    "alerts": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "NO"),
        (
            "type",
            "enum('low_water','low_battery','low_light','device_offline','failed_delivery','pump_shortfall')",
            "NO",
        ),
        ("raised_at", "datetime(3)", "NO"),
        ("cleared_at", "datetime(3)", "YES"),
        ("dismissed", "tinyint(1)", "NO"),
    ],
    "diagnoses": [
        ("id", "bigint unsigned", "NO"),
        ("plant_id", "bigint unsigned", "NO"),
        ("created_at", "datetime(3)", "NO"),
        ("photo_path", "varchar(500)", "NO"),
        ("thumbnail_path", "varchar(500)", "YES"),
        (
            "condition",
            "enum('healthy','underwatered','overwatered_or_root_rot','nutrient_deficiency','too_much_light','too_little_light','pests','fungal_or_leaf_spot','not_a_plant','unclear')",
            "NO",
        ),
        ("observation", "text", "YES"),
        ("check_yourself", "text", "YES"),
        ("search_term", "varchar(200)", "YES"),
        ("advice", "text", "YES"),
        ("provider", "varchar(50)", "NO"),
        ("raw_response", "mediumtext", "YES"),
        ("flagged_for_review", "tinyint(1)", "NO"),
    ],
    "reject_log": [
        ("id", "bigint unsigned", "NO"),
        ("serial", "varchar(32)", "NO"),
        ("received_at", "datetime(3)", "NO"),
        ("reason", "varchar(200)", "NO"),
        ("payload_excerpt", "varchar(500)", "YES"),
    ],
}

# Named indexes and unique keys in spec 9.2: table -> {index name: columns}.
EXPECTED_INDEXES = {
    "readings": {
        "idx_readings_plant_time": ["plant_id", "device_time"],
        "idx_readings_device_received": ["device_id", "received_at"],
    },
    "events": {"idx_events_plant_time": ["plant_id", "device_time"]},
    "cycles": {"uq_cycle": ["plant_id", "start_event_id"]},
}

# Columns declared UNIQUE in spec 9.2.
EXPECTED_UNIQUE_COLUMNS = [
    ("accounts", "email"),
    ("devices", "serial"),
    ("devices", "plant_id"),
    ("readings", "reading_id"),
    ("events", "event_id"),
]

# Every foreign key in spec 9.2: (table, column, referenced table). Only sessions cascades.
EXPECTED_FOREIGN_KEYS = {
    ("sessions", "account_id", "accounts"),
    ("plants", "account_id", "accounts"),
    ("plants", "species_id", "species"),
    ("devices", "account_id", "accounts"),
    ("devices", "plant_id", "plants"),
    ("calibrations", "plant_id", "plants"),
    ("calibrations", "device_id", "devices"),
    ("water_requests", "plant_id", "plants"),
    ("readings", "plant_id", "plants"),
    ("readings", "device_id", "devices"),
    ("events", "plant_id", "plants"),
    ("events", "device_id", "devices"),
    ("events", "request_id", "water_requests"),
    ("data_gaps", "device_id", "devices"),
    ("data_gaps", "plant_id", "plants"),
    ("cycles", "plant_id", "plants"),
    ("model_fits", "plant_id", "plants"),
    ("alerts", "plant_id", "plants"),
    ("diagnoses", "plant_id", "plants"),
}


def query(sql, **params):
    with get_engine().connect() as conn:
        return [tuple(r) for r in conn.execute(text(sql), params)]


def test_all_fifteen_tables_exist():
    with get_engine().connect() as conn:
        assert sorted(app_tables(conn)) == sorted(EXPECTED_COLUMNS)
    assert len(EXPECTED_COLUMNS) == 15


def test_every_column_matches_spec():
    for table, expected in EXPECTED_COLUMNS.items():
        got = query(
            "SELECT column_name, column_type, is_nullable FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = :t ORDER BY ordinal_position",
            t=table,
        )
        assert got == expected, f"columns of {table} differ from spec 9.2"


def test_named_indexes_and_unique_keys_exist():
    for table, indexes in EXPECTED_INDEXES.items():
        for name, columns in indexes.items():
            got = query(
                "SELECT column_name FROM information_schema.statistics "
                "WHERE table_schema = DATABASE() AND table_name = :t AND index_name = :i "
                "ORDER BY seq_in_index",
                t=table,
                i=name,
            )
            assert [r[0] for r in got] == columns, f"index {name} on {table}"
    unique = query(
        "SELECT table_name, index_name, GROUP_CONCAT(column_name ORDER BY seq_in_index) "
        "FROM information_schema.statistics WHERE table_schema = DATABASE() AND non_unique = 0 "
        "GROUP BY table_name, index_name"
    )
    single_unique = {(t, cols) for t, _name, cols in unique}
    for table, column in EXPECTED_UNIQUE_COLUMNS:
        assert (table, column) in single_unique, f"{table}.{column} should be UNIQUE"
    assert ("cycles", "plant_id,start_event_id") in single_unique


def test_foreign_keys_match_spec():
    got = query(
        "SELECT k.table_name, k.column_name, k.referenced_table_name, r.delete_rule "
        "FROM information_schema.key_column_usage k "
        "JOIN information_schema.referential_constraints r "
        "  ON r.constraint_schema = k.constraint_schema AND r.constraint_name = k.constraint_name "
        "WHERE k.table_schema = DATABASE() AND k.referenced_table_name IS NOT NULL"
    )
    assert {(t, c, ref) for t, c, ref, _rule in got} == EXPECTED_FOREIGN_KEYS
    for table, column, _ref, rule in got:
        # Spec 9.2: ON DELETE RESTRICT unless noted. InnoDB reports an unstated rule as
        # NO ACTION, which behaves the same as RESTRICT.
        expected_rule = "CASCADE" if table == "sessions" else "NO ACTION"
        assert rule == expected_rule, f"{table}.{column} delete rule"


def test_tables_are_innodb_utf8mb4():
    # Spec 9: "MySQL 8.4 LTS, InnoDB, utf8mb4". The 9.2 statements don't name these, so
    # this checks MySQL's defaults gave the tables both.
    got = query(
        "SELECT table_name, engine, table_collation FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name <> 'alembic_version'"
    )
    for table, engine, collation in got:
        assert engine == "InnoDB", table
        assert collation.startswith("utf8mb4"), table


def test_models_match_the_migrated_schema():
    with get_engine().connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        differences = compare_metadata(context, Base.metadata)
    assert differences == []


def test_downgrade_removes_every_table_and_upgrade_restores_them():
    config = alembic_config()
    command.downgrade(config, "base")
    try:
        with get_engine().connect() as conn:
            assert app_tables(conn) == []
    finally:
        command.upgrade(config, "head")
    with get_engine().connect() as conn:
        assert sorted(app_tables(conn)) == sorted(EXPECTED_COLUMNS)
