"""Initial schema: every table in spec 9.2, in the spec's creation order.

Each CREATE TABLE statement is copied exactly from spec 9.2 (docs/Sprout Master
Specification v3.md), so names, types, NULL / NOT NULL, defaults, ENUM values, keys,
indexes and foreign keys match the spec. Change them only through the spec.

Revision ID: 0001
Revises:
Create Date: 2026-11-16
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# (table name, CREATE TABLE statement), in creation order (spec 9.2).
TABLES = [
    (
        "accounts",
        """
CREATE TABLE accounts (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,                 -- argon2
  timezone VARCHAR(64) NOT NULL DEFAULT 'America/Los_Angeles',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
);
""",
    ),
    (
        "sessions",
        """
CREATE TABLE sessions (
  id CHAR(64) PRIMARY KEY,                             -- SHA-256 of the cookie token
  account_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(3) NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);
""",
    ),
    (
        "species",
        """
CREATE TABLE species (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  common_name VARCHAR(100) NOT NULL,
  scientific_name VARCHAR(150) NOT NULL,
  days_between_waterings DECIMAL(4,1) NOT NULL,
  light_hours DECIMAL(3,1) NOT NULL,
  water_threshold_pct DECIMAL(4,1) NOT NULL,
  source_url VARCHAR(500) NOT NULL,
  toxic_to_cats TINYINT(1) NULL,
  toxic_to_dogs TINYINT(1) NULL,
  perenual_id INT NULL,                                -- B7
  image_url VARCHAR(500) NULL,                         -- B7
  care_text TEXT NULL                                  -- B7, display only
);
""",
    ),
    (
        "plants",
        """
CREATE TABLE plants (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  account_id BIGINT UNSIGNED NOT NULL,
  species_id INT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  dry_raw INT NULL,                                    -- current calibration; NULL = none
  wet_raw INT NULL,
  moisture_threshold DECIMAL(4,1) NOT NULL,            -- copied from species at creation
  target_ml DECIMAL(6,1) NOT NULL DEFAULT 60.0,        -- DEC-12
  jar_capacity_ml INT NOT NULL,
  ml_since_refill DECIMAL(8,1) NOT NULL DEFAULT 0,
  effective_interval_h DECIMAL(6,1) NULL,              -- last value used, for the 25% limit
  learning_epoch INT UNSIGNED NOT NULL DEFAULT 1,
  epoch_started_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  epoch_reason ENUM('created','repot','moved','soil_change','other') NOT NULL DEFAULT 'created', -- Q15
  is_simulated TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (species_id) REFERENCES species(id)
);
""",
    ),
    (
        "devices",
        """
CREATE TABLE devices (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  serial VARCHAR(32) NOT NULL UNIQUE,
  key_hash VARCHAR(255) NOT NULL,                      -- argon2 hash of the device key
  claim_code_hash VARCHAR(255) NULL,                   -- NULL once burned
  claimed_at DATETIME(3) NULL,
  account_id BIGINT UNSIGNED NULL,
  plant_id BIGINT UNSIGNED NULL UNIQUE,
  name VARCHAR(100) NULL,
  ml_per_s DECIMAL(5,2) NULL,                          -- measured at G11
  firmware_version VARCHAR(32) NULL,
  last_seen DATETIME(3) NULL,
  retired_at DATETIME(3) NULL,                         -- set while retired (a pause, 8.5.1); NULL = active
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);
""",
    ),
    (
        "calibrations",
        """
CREATE TABLE calibrations (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  device_id BIGINT UNSIGNED NULL,
  dry_raw INT NULL,                                    -- both NULL = calibration cleared (R-19)
  wet_raw INT NULL,
  reason ENUM('setup','recalibration','repot','sensor_replaced','reassigned') NOT NULL,
  set_at DATETIME(3) NOT NULL,
  FOREIGN KEY (plant_id) REFERENCES plants(id),
  FOREIGN KEY (device_id) REFERENCES devices(id)
);
""",
    ),
    (
        "water_requests",
        """
CREATE TABLE water_requests (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  requested_at DATETIME(3) NOT NULL,
  sent_at DATETIME(3) NULL,                            -- first config reply that carried it
  resolved_at DATETIME(3) NULL,
  outcome ENUM('pending','delivered','refused','expired') NOT NULL DEFAULT 'pending',
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);
""",
    ),
    (
        "readings",
        """
CREATE TABLE readings (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NULL,                       -- NULL until the stake is set up (8.5)
  device_id BIGINT UNSIGNED NOT NULL,
  reading_id VARCHAR(40) NOT NULL UNIQUE,
  boot_id INT UNSIGNED NOT NULL,
  uptime_s INT UNSIGNED NOT NULL,
  device_time DATETIME(3) NULL,
  time_status ENUM('synced','estimated','unknown') NOT NULL,
  received_at DATETIME(3) NOT NULL,
  moisture_raw INT NOT NULL,
  moisture_pct DECIMAL(4,1) NULL,
  sensor_fault TINYINT(1) NOT NULL DEFAULT 0,
  lux INT UNSIGNED NULL,
  battery_mv INT NOT NULL,
  reservoir_low TINYINT(1) NOT NULL,
  soil_temp_c DECIMAL(4,1) NULL,                       -- reserved; always NULL in v1 (DEC-08)
  INDEX idx_readings_plant_time (plant_id, device_time),
  INDEX idx_readings_device_received (device_id, received_at),
  FOREIGN KEY (plant_id) REFERENCES plants(id),
  FOREIGN KEY (device_id) REFERENCES devices(id)
);
""",
    ),
    (
        "events",
        """
CREATE TABLE events (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NULL,
  device_id BIGINT UNSIGNED NOT NULL,
  event_id VARCHAR(40) NOT NULL UNIQUE,
  boot_id INT UNSIGNED NOT NULL,
  uptime_s INT UNSIGNED NOT NULL,
  device_time DATETIME(3) NULL,
  time_status ENUM('synced','estimated','unknown') NOT NULL,
  received_at DATETIME(3) NOT NULL,
  duration_ms INT UNSIGNED NOT NULL,
  volume_ml DECIMAL(6,1) NULL,                         -- computed; NULL until ml_per_s is known
  trigger_type ENUM('auto','manual','test') NOT NULL,
  request_id BIGINT UNSIGNED NULL,
  moisture_before DECIMAL(4,1) NULL,
  delivery ENUM('ok','failed','unchecked','refused') NOT NULL,
  INDEX idx_events_plant_time (plant_id, device_time),
  FOREIGN KEY (plant_id) REFERENCES plants(id),
  FOREIGN KEY (device_id) REFERENCES devices(id),
  FOREIGN KEY (request_id) REFERENCES water_requests(id)
);
""",
    ),
    (
        "data_gaps",
        """
CREATE TABLE data_gaps (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  device_id BIGINT UNSIGNED NOT NULL,
  plant_id BIGINT UNSIGNED NULL,
  received_at DATETIME(3) NOT NULL,
  dropped_count INT UNSIGNED NOT NULL,
  gap_start DATETIME(3) NULL,                          -- latest stored reading before the gap
  gap_end DATETIME(3) NULL,                            -- oldest reading in the batch
  FOREIGN KEY (device_id) REFERENCES devices(id),
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);
""",
    ),
    (
        "cycles",
        """
CREATE TABLE cycles (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  epoch INT UNSIGNED NOT NULL,
  start_event_id BIGINT UNSIGNED NOT NULL,             -- events.id
  end_event_id BIGINT UNSIGNED NOT NULL,
  start_time DATETIME(3) NOT NULL,
  end_time DATETIME(3) NOT NULL,
  start_pct DECIMAL(4,1) NULL,
  end_pct DECIMAL(4,1) NULL,
  hours DECIMAL(7,2) NOT NULL,
  hours_to_threshold DECIMAL(7,2) NULL,
  rate_pct_per_hour DECIMAL(6,3) NULL,
  mean_daily_lux INT NULL,
  valid TINYINT(1) NOT NULL,
  exclusion_reason ENUM('manual_or_test_watering','failed_or_refused_event','sensor_fault',
    'reading_gap','data_gap_reported','unknown_time','too_few_readings',
    'non_positive_rate','calibration_changed','other') NULL,
  computed_at DATETIME(3) NOT NULL,
  UNIQUE KEY uq_cycle (plant_id, start_event_id),
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);
""",
    ),
    (
        "model_fits",
        """
CREATE TABLE model_fits (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  epoch INT UNSIGNED NOT NULL,
  fitted_at DATETIME(3) NOT NULL,
  model_type ENUM('mean_interval','regression') NOT NULL,   -- DEC-24
  model_version VARCHAR(20) NOT NULL,
  in_use TINYINT(1) NOT NULL DEFAULT 0,                -- the fit that set effective_interval_h
  learned_interval_h DOUBLE NULL,
  intercept DOUBLE NULL,
  light_coef DOUBLE NULL,
  temp_coef DOUBLE NULL,                               -- reserved; always NULL in v1
  r2 DOUBLE NULL,
  cycle_count INT UNSIGNED NOT NULL,
  mae_learned_h DOUBLE NULL,                           -- G31: learned pipeline
  mae_species_h DOUBLE NULL,                           -- G31: species default
  mae_mean_h DOUBLE NULL,                              -- simple average, for the DEC-24 switch
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);
""",
    ),
    (
        "alerts",
        """
CREATE TABLE alerts (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  type ENUM('low_water','low_battery','low_light','device_offline',
            'failed_delivery','pump_shortfall') NOT NULL,
  raised_at DATETIME(3) NOT NULL,
  cleared_at DATETIME(3) NULL,
  dismissed TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);
""",
    ),
    (
        "diagnoses",
        """
CREATE TABLE diagnoses (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(3) NOT NULL,
  photo_path VARCHAR(500) NOT NULL,
  thumbnail_path VARCHAR(500) NULL,
  `condition` ENUM('healthy','underwatered','overwatered_or_root_rot',
    'nutrient_deficiency','too_much_light','too_little_light','pests',
    'fungal_or_leaf_spot','not_a_plant','unclear') NOT NULL,
  observation TEXT NULL,
  check_yourself TEXT NULL,
  search_term VARCHAR(200) NULL,
  advice TEXT NULL,
  provider VARCHAR(50) NOT NULL,
  raw_response MEDIUMTEXT NULL,                        -- stored on every call, failures too
  flagged_for_review TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);
""",
    ),
    (
        "reject_log",
        """
CREATE TABLE reject_log (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  serial VARCHAR(32) NOT NULL,
  received_at DATETIME(3) NOT NULL,
  reason VARCHAR(200) NOT NULL,
  payload_excerpt VARCHAR(500) NULL
);
""",
    ),
]


def upgrade() -> None:
    for _name, create_sql in TABLES:
        op.execute(create_sql)


def downgrade() -> None:
    for name, _create_sql in reversed(TABLES):
        op.execute(f"DROP TABLE {name}")
