"""The data simulator (spec 10.7, task card B2).

Writes eight weeks of messy hourly readings for three simulated plants, SIM-001 to SIM-003,
into a development database, only through ingest_batch (the path POST /api/readings uses),
and writes sim_truth.json with the true values. Random seed 42.

Run it from server/ after the migrations and the seed (app.seed):

    uv run python ../tools/simulate/simulate.py

Values the spec doesn't give are marked PLACEHOLDER below. Every one is listed in the B2
pull request; the simulator only makes development data, so they are low risk.
"""

import argparse
import json
import math
import secrets
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.ingest import ingest_batch
from app.models import Account, Calibration, Device, Plant, Species, WaterRequest
from app.schemas.upload import ReadingsUpload

SEED = 42
DAYS = 56  # eight weeks
LOCAL_TZ = ZoneInfo("America/Los_Angeles")  # the seeded account's time zone (spec 9.2 default)

# Spec 10.7
START_PCT = 80.0
WATER_AT_PCT = 30.0
WATER_ADD_PCT = 50.0
WATER_CAP_PCT = 90.0
AUTO_PUMP_MS = 8400
NOISE_SD = 1.5
DRY_RAW, WET_RAW = 2650, 1180
PEAK_LUX = 10_000
DROP_FRACTION = 0.02
OUTAGE_HOURS = 14
FAULT_RUN = 6
WINDOW_START = (11, 30)  # 11:30 local
WINDOW_MINUTES = 70  # to 12:40 local

# The team's readings of the unclear 10.7 items (task card B2, section 4).
RECAL_DRY_RAW, RECAL_WET_RAW = 2600, 1200

# PLACEHOLDERS: values the spec doesn't give (task card B2, section 9).
SPECIES_SCIENTIFIC_NAME = "Ocimum basilicum"  # question 1: basil
JAR_CAPACITY_ML = 1000  # question 2: the spec 13.2 example jar size
BATTERY_MV = 3900  # not in 10.7: a steady, healthy battery
FIRMWARE_VERSION = "1.0.0-sim"
FAULT_RAW = 4095  # a fault reading: probe outside its sanity range (8.3 sensor_fault)
TRUTH_PATH = (
    Path(__file__).resolve().parents[2] / "tools" / "simulate" / "output" / "sim_truth.json"
)

PLANTS = [
    # name, stake serial, rate rule (spec 10.7)
    ("SIM-001", "SPROUT-901", "0.5 + 0.00008 * mean daily lux"),
    ("SIM-002", "SPROUT-902", "0.3 + 0.00005 * mean daily lux"),
    ("SIM-003", "SPROUT-903", "SIM-001's rate * (moisture - 10) / 50"),
]


def rate_for(name: str, mean_lux: float, moisture: float) -> float:
    """Points of moisture lost per hour (spec 10.7, "True drying rate")."""
    if name == "SIM-001":
        return 0.5 + 0.00008 * mean_lux
    if name == "SIM-002":
        return 0.3 + 0.00005 * mean_lux
    return (0.5 + 0.00008 * mean_lux) * (moisture - 10) / 50


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def local(t: datetime) -> datetime:
    return t.replace(tzinfo=UTC).astimezone(LOCAL_TZ)


@dataclass
class PlantPlan:
    name: str
    serial: str
    rate_rule: str
    readings: list[dict] = field(default_factory=list)  # one per hour, dropped ones included
    events: list[dict] = field(default_factory=list)
    recal_at: datetime | None = None
    manual_request_at: datetime | None = None  # the upload that carries the water request
    cycles: list[dict] = field(default_factory=list)


@dataclass
class Simulation:
    seed: int
    start: datetime
    end: datetime
    hours: list[datetime]
    uploads: list[datetime]
    outage: tuple[datetime, datetime]
    zero_lux_date: str
    plants: list[PlantPlan]

    def truth(self) -> dict:
        return {
            "seed": self.seed,
            "start": iso(self.start),
            "end": iso(self.end),
            "time_zone": str(LOCAL_TZ),
            "network_outage": {"start": iso(self.outage[0]), "end": iso(self.outage[1])},
            "zero_lux_local_date": self.zero_lux_date,
            "plants": [
                {
                    "name": p.name,
                    "serial": p.serial,
                    "true_rate_rule": p.rate_rule,
                    "recalibrated_at": iso(p.recal_at) if p.recal_at else None,
                    "cycles": p.cycles,
                }
                for p in self.plants
            ],
        }


def _upload_times(rng, start: datetime, end: datetime, outage) -> list[datetime]:
    """One upload each weekday between 11:30 and 12:40 local, none at weekends (10.7)."""
    times = []
    day = local(start).date()
    while True:
        midnight = datetime(day.year, day.month, day.day, tzinfo=LOCAL_TZ)
        if midnight.astimezone(UTC).replace(tzinfo=None) > end:
            break
        minute = int(rng.integers(0, WINDOW_MINUTES + 1))
        if day.weekday() < 5:
            t_local = midnight.replace(hour=WINDOW_START[0], minute=WINDOW_START[1]) + timedelta(
                minutes=minute
            )
            t = t_local.astimezone(UTC).replace(tzinfo=None)
            if start < t <= end and not (outage[0] <= t < outage[1]):
                times.append(t)
        day += timedelta(days=1)
    return times


def generate(seed: int = SEED, end: datetime | None = None) -> Simulation:
    """Work out the whole simulation in memory. The same seed and end give the same result."""
    if end is None:
        end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    rng = np.random.default_rng(seed)
    start = end - timedelta(days=DAYS)
    hours = [start + timedelta(hours=i) for i in range(DAYS * 24)]

    # Light: one weather for all three plants (they share a windowsill).
    local_dates = sorted({local(t).date() for t in hours})
    peak = {d: PEAK_LUX * float(rng.uniform(0.4, 1.0)) for d in local_dates}
    zero_lux_date = local_dates[int(rng.integers(10, len(local_dates) - 10))]

    def lux_at(t: datetime) -> int:
        lt = local(t)
        if lt.date() == zero_lux_date:
            return 0
        h = lt.hour + lt.minute / 60
        if 6 <= h < 18:
            return round(peak[lt.date()] * math.sin(math.pi * (h - 6) / 12))
        return 0

    lux = [lux_at(t) for t in hours]
    by_date: dict = {}
    for t, value in zip(hours, lux, strict=True):
        by_date.setdefault(local(t).date(), []).append(value)
    mean_lux = {d: sum(v) / len(v) for d, v in by_date.items()}

    # One 14-hour network outage, covering a weekday's sync window (task card B2).
    weekdays = [d for d in local_dates[7:-7] if d.weekday() < 5]
    outage_day = weekdays[int(rng.integers(0, len(weekdays)))]
    outage_start_local = datetime(
        outage_day.year, outage_day.month, outage_day.day, 5, 0, tzinfo=LOCAL_TZ
    )
    outage_start = outage_start_local.astimezone(UTC).replace(tzinfo=None)
    outage = (outage_start, outage_start + timedelta(hours=OUTAGE_HOURS))
    uploads = _upload_times(rng, start, end, outage)

    boot_time = start - timedelta(hours=1)
    plants = []
    for name, serial, rule in PLANTS:
        p = PlantPlan(name=name, serial=serial, rate_rule=rule)
        n = len(hours)
        dropped = rng.random(n) < DROP_FRACTION
        fault_start = int(rng.integers(n // 8, n - FAULT_RUN - n // 8))
        fault = set(range(fault_start, fault_start + FAULT_RUN))
        recal_index = n // 2
        p.recal_at = hours[recal_index]
        manual_upload = uploads[len(uploads) // 3]
        p.manual_request_at = manual_upload
        manual_index = next(i for i, t in enumerate(hours) if t > manual_upload)

        moisture = START_PCT
        rates = []
        event_hours = []
        last_measured = None
        for i, t in enumerate(hours):
            dry, wet = (DRY_RAW, WET_RAW) if i < recal_index else (RECAL_DRY_RAW, RECAL_WET_RAW)
            if i in fault:
                pct, raw = None, FAULT_RAW
            else:
                pct = round(min(100.0, max(0.0, moisture + float(rng.normal(0, NOISE_SD)))), 1)
                raw = round(dry - pct / 100 * (dry - wet))
                last_measured = pct
            p.readings.append(
                {
                    "i": i,
                    "t": t,
                    "dropped": bool(dropped[i]),
                    "uptime_s": int((t - boot_time).total_seconds()),
                    "moisture_raw": raw,
                    "moisture_pct": pct,
                    "lux": lux[i],
                    "sensor_fault": i in fault,
                    "true_moisture": round(moisture, 3),
                }
            )
            trigger = None
            if i == manual_index:
                trigger = "manual"
            elif moisture <= WATER_AT_PCT:
                trigger = "auto"
            if trigger:
                p.events.append(
                    {
                        "i": i,
                        "t": t + timedelta(minutes=1),
                        "uptime_s": int((t - boot_time).total_seconds()) + 60,
                        "trigger": trigger,
                        "duration_ms": AUTO_PUMP_MS,
                        "moisture_before": last_measured,
                    }
                )
                event_hours.append((i, trigger))
                moisture = min(moisture + WATER_ADD_PCT, WATER_CAP_PCT)
            r = rate_for(name, mean_lux[local(t).date()], moisture)
            rates.append(r)
            moisture -= r

        # Truth per cycle: the true mean drying rate over the readings a fit uses
        # (spec 11.2: from 2 hours after the first watering up to the second).
        for (a, trig_a), (b, trig_b) in zip(event_hours, event_hours[1:], strict=False):
            first, last = a + 2, b
            window = range(first, last + 1)
            messy = sorted(
                {
                    *(["dropped_reading"] if any(dropped[k] for k in window) else []),
                    *(["sensor_fault"] if any(k in fault for k in window) else []),
                    *(["calibration_change"] if first <= recal_index <= last else []),
                    *(["manual_watering"] if "manual" in (trig_a, trig_b) else []),
                }
            )
            p.cycles.append(
                {
                    "start": iso(hours[a]),
                    "end": iso(hours[b]),
                    "fit_from": iso(hours[first]),
                    "true_rate_pct_per_hour": round(float(np.mean(rates[first:last])), 6),
                    "mess": messy,
                }
            )
        plants.append(p)

    return Simulation(
        seed=seed,
        start=start,
        end=end,
        hours=hours,
        uploads=uploads,
        outage=outage,
        zero_lux_date=zero_lux_date.isoformat(),
        plants=plants,
    )


def _status(t: datetime, last_sync: datetime) -> str:
    """Spec 7.6: synced within 24 hours of the last clock sync, else estimated."""
    return "synced" if t - last_sync <= timedelta(hours=24) else "estimated"


def _upload_body(p: PlantPlan, readings, events, sent: datetime, uptime_s: int) -> ReadingsUpload:
    return ReadingsUpload.model_validate(
        {
            "serial": p.serial,
            "firmware_version": FIRMWARE_VERSION,
            "sent_time": iso(sent),
            "sent_boot_id": 1,
            "sent_uptime_s": uptime_s,
            "dropped_count": 0,
            "readings": readings,
            "events": events,
        }
    )


class SimulatorRefused(Exception):
    """The simulator won't run against this database. The message says why."""


def run(session: Session, sim: Simulation) -> dict:
    """Write the simulation into the database through ingest_batch. Returns counts."""
    real = session.scalar(select(Plant.id).where(Plant.is_simulated == 0).limit(1))
    if real is not None:
        raise SimulatorRefused(
            "This database holds real (non-simulated) plants. The simulator only writes to a "
            "development database (spec 5.2)."
        )
    names = [name for name, _, _ in PLANTS]
    if session.scalar(select(Plant.id).where(Plant.name.in_(names)).limit(1)) is not None:
        raise SimulatorRefused("SIM-001 to SIM-003 already exist here; nothing was added.")
    account = session.get(Account, 1)
    if account is None:
        raise SimulatorRefused("The seeded account (id 1) is missing. Run app.seed first.")
    species = session.scalar(
        select(Species).where(Species.scientific_name == SPECIES_SCIENTIFIC_NAME).limit(1)
    )
    if species is None:
        raise SimulatorRefused(f"No {SPECIES_SCIENTIFIC_NAME} species row. Run app.seed first.")

    hasher = PasswordHasher()
    devices = {}
    plants = {}
    for p in sim.plants:
        plant = Plant(
            account_id=account.id,
            species_id=species.id,
            name=p.name,
            dry_raw=DRY_RAW,
            wet_raw=WET_RAW,
            moisture_threshold=species.water_threshold_pct,
            jar_capacity_ml=JAR_CAPACITY_ML,
            epoch_started_at=sim.start,
            is_simulated=1,
            created_at=sim.start,
        )
        session.add(plant)
        session.flush()
        device = Device(
            serial=p.serial,
            # A random key nobody knows: simulated stakes never post over HTTP.
            key_hash=hasher.hash(secrets.token_urlsafe(32)),
            account_id=account.id,
            plant_id=plant.id,
            name=f"{p.name} (simulated)",
        )
        session.add(device)
        session.flush()
        session.add(
            Calibration(
                plant_id=plant.id,
                device_id=device.id,
                dry_raw=DRY_RAW,
                wet_raw=WET_RAW,
                reason="setup",
                set_at=sim.start,
            )
        )
        plants[p.name], devices[p.name] = plant, device
    session.commit()

    boot_time = sim.start - timedelta(hours=1)
    counts = {
        p.name: {"readings_stored": 0, "readings_dropped": 0, "events_stored": 0}
        for p in sim.plants
    }
    for p in sim.plants:
        plant, device = plants[p.name], devices[p.name]
        last_sync = sim.start  # provisioned with a set clock
        statuses = {}
        for r in p.readings:
            synced_before = [u for u in sim.uploads if u <= r["t"]]
            statuses[r["i"]] = _status(r["t"], synced_before[-1] if synced_before else last_sync)
        sent_r = 0
        sent_e = 0
        request_id = None
        recal_done = False
        for upload_at in sim.uploads:
            if not recal_done and p.recal_at <= upload_at:
                plant.dry_raw, plant.wet_raw = RECAL_DRY_RAW, RECAL_WET_RAW
                session.add(
                    Calibration(
                        plant_id=plant.id,
                        device_id=device.id,
                        dry_raw=RECAL_DRY_RAW,
                        wet_raw=RECAL_WET_RAW,
                        reason="recalibration",
                        set_at=p.recal_at,
                    )
                )
                recal_done = True
            readings = []
            while sent_r < len(p.readings) and p.readings[sent_r]["t"] <= upload_at:
                r = p.readings[sent_r]
                sent_r += 1
                if r["dropped"]:
                    counts[p.name]["readings_dropped"] += 1
                    continue
                readings.append(
                    {
                        "reading_id": f"{p.serial}-{r['i'] + 1:06d}",
                        "boot_id": 1,
                        "uptime_s": r["uptime_s"],
                        "device_time": iso(r["t"]),
                        "time_status": statuses[r["i"]],
                        "moisture_raw": r["moisture_raw"],
                        "moisture_pct": r["moisture_pct"],
                        "lux": r["lux"],
                        "battery_mv": BATTERY_MV,
                        "reservoir_low": False,
                        "sensor_fault": r["sensor_fault"],
                        "soil_temp_c": None,
                    }
                )
            events = []
            while sent_e < len(p.events) and p.events[sent_e]["t"] <= upload_at:
                e = p.events[sent_e]
                sent_e += 1
                events.append(
                    {
                        "event_id": f"{p.serial}-E{sent_e:06d}",
                        "boot_id": 1,
                        "uptime_s": e["uptime_s"],
                        "device_time": iso(e["t"]),
                        "time_status": _status(e["t"], last_sync),
                        "duration_ms": e["duration_ms"],
                        "trigger": e["trigger"],
                        "request_id": request_id if e["trigger"] == "manual" else None,
                        "moisture_before": e["moisture_before"],
                        "delivery": "ok",  # PLACEHOLDER (card question 5)
                    }
                )
            uptime = int((upload_at - boot_time).total_seconds())
            body = _upload_body(p, readings, events, upload_at, uptime)
            result = ingest_batch(session, device, body, received_at=upload_at)
            counts[p.name]["readings_stored"] += result.readings_stored
            counts[p.name]["events_stored"] += result.events_stored
            last_sync = upload_at
            if upload_at == p.manual_request_at:
                # Water now, pressed before this sync: the config reply carries the request
                # (10.3), and the stake waters at its next wake (7.3).
                req = WaterRequest(
                    plant_id=plant.id,
                    requested_at=upload_at - timedelta(minutes=30),
                    sent_at=upload_at,
                    outcome="pending",
                )
                session.add(req)
                session.flush()
                request_id = req.id
            session.commit()
    return counts


def write_truth(sim: Simulation, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sim.truth(), indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write eight weeks of simulated plant data.")
    parser.add_argument(
        "--end",
        help="UTC date the eight weeks end on, as YYYY-MM-DD (default: today). Same date, "
        "same data.",
    )
    parser.add_argument(
        "--truth", type=Path, default=TRUTH_PATH, help="Where to write sim_truth.json"
    )
    args = parser.parse_args(argv)
    end = datetime.strptime(args.end, "%Y-%m-%d") if args.end else None
    sim = generate(SEED, end)
    session = get_session()
    try:
        counts = run(session, sim)
    except SimulatorRefused as e:
        session.rollback()
        print(f"Simulator stopped: {e}", file=sys.stderr)
        return 1
    finally:
        session.close()
    write_truth(sim, args.truth)
    print(f"Simulated {iso(sim.start)} to {iso(sim.end)} (seed {sim.seed}).")
    for name, c in counts.items():
        print(
            f"  {name}: {c['readings_stored']} readings stored, {c['readings_dropped']} dropped, "
            f"{c['events_stored']} waterings"
        )
    print(f"Truth file: {args.truth}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
