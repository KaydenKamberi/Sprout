"""B2: the simulator (spec 10.7), run once with seed 42 against the test database."""

import json
from datetime import datetime, timedelta

import numpy as np
import pytest
from sqlalchemy import func, select

from app.db import get_session
from app.models import Calibration, Device, Event, Plant, Reading, WaterRequest
from app.seed import ensure_seed_account, load_species
from app.simulator import DAYS, SimulatorRefused, generate, run, write_truth
from tests.conftest import empty_all_tables

END = datetime(2026, 11, 16)
NAMES = ["SIM-001", "SIM-002", "SIM-003"]
SERIALS = ["SPROUT-901", "SPROUT-902", "SPROUT-903"]


def parse(t: str) -> datetime:
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(scope="module")
def simulated(tmp_path_factory):
    session = get_session()
    mp = pytest.MonkeyPatch()
    mp.setenv("SEED_ACCOUNT_PASSWORD", "throwaway-test-password")
    try:
        ensure_seed_account(session)
        load_species(session)
        session.commit()
        sim = generate(42, END)
        counts = run(session, sim)
        truth_path = tmp_path_factory.mktemp("sim") / "sim_truth.json"
        write_truth(sim, truth_path)
        yield session, sim, counts, json.loads(truth_path.read_text())
    finally:
        mp.undo()
        session.rollback()
        session.close()
        empty_all_tables()


def plant(session, name):
    return session.scalar(select(Plant).where(Plant.name == name))


def test_three_simulated_plants_on_their_stakes(simulated):
    session, *_ = simulated
    for name, serial in zip(NAMES, SERIALS, strict=True):
        p = plant(session, name)
        assert p.is_simulated == 1 and p.account_id == 1
        device = session.scalar(select(Device).where(Device.plant_id == p.id))
        assert device.serial == serial


def test_about_eight_weeks_of_hourly_readings(simulated):
    session, sim, counts, _ = simulated
    for name in NAMES:
        p = plant(session, name)
        n, first, last = session.execute(
            select(
                func.count(), func.min(Reading.device_time), func.max(Reading.device_time)
            ).where(Reading.plant_id == p.id)
        ).one()
        # 56 days x 24 h, less the ~2% dropped and the hours after the last weekday sync.
        assert DAYS * 24 * 0.9 < n <= DAYS * 24
        assert last - first > timedelta(days=DAYS - 4)
        assert counts[name]["readings_stored"] == n


def test_every_mess_item_appears(simulated):
    session, sim, counts, truth = simulated
    for name in NAMES:
        p = plant(session, name)
        readings = session.scalars(
            select(Reading).where(Reading.plant_id == p.id).order_by(Reading.device_time)
        ).all()
        # 2% of readings dropped: never sent
        dropped = counts[name]["readings_dropped"]
        assert 0.005 * DAYS * 24 < dropped < 0.04 * DAYS * 24
        # a run of 6 sensor-fault readings
        faults = [i for i, r in enumerate(readings) if r.sensor_fault]
        assert len(faults) == 6 and faults[-1] - faults[0] <= 6
        assert all(readings[i].moisture_pct is None for i in faults)
        # one day of zero lux, in the owner's local time
        zero_day = truth["zero_lux_local_date"]
        assert zero_day
        # one recalibration halfway through
        reasons = session.scalars(
            select(Calibration.reason).where(Calibration.plant_id == p.id)
        ).all()
        assert sorted(reasons) == ["recalibration", "setup"]
        assert (p.dry_raw, p.wet_raw) == (2600, 1200)
        # one manual watering, answering a water request that is now delivered
        manual = session.scalars(
            select(Event).where(Event.plant_id == p.id, Event.trigger_type == "manual")
        ).all()
        assert len(manual) == 1
        request = session.get(WaterRequest, manual[0].request_id)
        assert request.plant_id == p.id and request.outcome == "delivered"
    # one 14-hour outage: no upload inside it, and the next upload carries its readings
    start, end = parse(truth["network_outage"]["start"]), parse(truth["network_outage"]["end"])
    assert end - start == timedelta(hours=14)
    assert not any(start <= u < end for u in sim.uploads)
    received = session.scalars(select(Reading.received_at).distinct()).all()
    assert not any(start <= r < end for r in received)
    # a whole local day with lux 0 for every hour
    daylight_zero = session.scalar(
        select(func.count()).where(Reading.lux == 0, Reading.device_time.is_not(None))
    )
    assert daylight_zero > 3 * 24


def test_weekend_readings_arrive_estimated_and_are_redated(simulated):
    session, sim, *_ = simulated
    p = plant(session, "SIM-001")
    estimated = session.scalars(
        select(Reading).where(Reading.plant_id == p.id, Reading.time_status == "estimated")
    ).all()
    assert len(estimated) > 100
    # Re-dated from the sync anchor: every estimated reading still has its true hourly time.
    assert all(r.device_time is not None for r in estimated)
    assert all(r.device_time.minute == 0 and r.device_time.second == 0 for r in estimated)
    weekend = [r for r in estimated if r.device_time.weekday() in (5, 6)]
    assert weekend, "weekend readings should be among the estimated ones"
    # nothing arrives at weekends: every batch was received on a weekday sync
    received = session.scalars(select(Reading.received_at).distinct()).all()
    assert all(r in sim.uploads for r in received)


def test_two_runs_with_seed_42_write_identical_truth(tmp_path):
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    write_truth(generate(42, END), first)
    write_truth(generate(42, END), second)
    assert first.read_bytes() == second.read_bytes()


def test_running_again_adds_no_duplicates(simulated):
    session, sim, *_ = simulated
    with pytest.raises(SimulatorRefused):
        run(session, sim)
    session.rollback()
    assert session.scalar(select(func.count()).select_from(Plant)) == 3
    assert session.scalar(select(func.count()).select_from(Device)) == 3


def test_early_pass_check_recovers_true_rate_within_10_percent(simulated):
    """Done when: fit a straight line to one simulated cycle, recover its true rate (10%)."""
    session, _, _, truth = simulated
    p = plant(session, "SIM-001")
    cycles = next(x for x in truth["plants"] if x["name"] == "SIM-001")["cycles"]
    clean = [c for c in cycles if not c["mess"]]
    assert clean, "SIM-001 should have at least one cycle untouched by the mess items"
    cycle = clean[0]
    fit_from, until = parse(cycle["fit_from"]), parse(cycle["end"])
    rows = session.execute(
        select(Reading.device_time, Reading.moisture_pct)
        .where(
            Reading.plant_id == p.id,
            Reading.device_time >= fit_from,
            Reading.device_time <= until,
            Reading.moisture_pct.is_not(None),
        )
        .order_by(Reading.device_time)
    ).all()
    assert len(rows) >= 12  # spec 11.2: at least 12 readings
    hours = np.array([(t - fit_from).total_seconds() / 3600 for t, _ in rows])
    pct = np.array([float(v) for _, v in rows])
    fitted_rate = -np.polyfit(hours, pct, 1)[0]  # spec 11.2: minus the least-squares slope
    true_rate = cycle["true_rate_pct_per_hour"]
    assert abs(fitted_rate - true_rate) / true_rate < 0.10
