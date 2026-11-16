"""Export a simulated plant's last 14 days as dashboard mock data (task card B2, addition).

Writes two files in the exact response shapes of spec 13.2:

- sim-001-readings.json: GET /api/plants/:id/readings?days=14 (readings and gaps)
- sim-001-events.json:   GET /api/plants/:id/events?days=14

into web/src/api/mock/, where the dashboard's mock data lives (task card C1). Run it after
the simulator, from server/:

    uv run python ../tools/simulate/export_mock.py
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import DataGap, Event, Plant, Reading

MOCK_DIR = Path(__file__).resolve().parents[2] / "web" / "src" / "api" / "mock"
DAYS = 14


def _t(t: datetime) -> str:
    """UTC ISO-8601 ending in Z (spec 13.2 conventions)."""
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _num(v: Decimal | None) -> float | None:
    return None if v is None else float(v)


def export_plant(
    session: Session, plant_name: str = "SIM-001", days: int = DAYS
) -> tuple[dict, dict]:
    """The readings and events responses for the plant's last `days` days of stored data."""
    plant = session.scalar(select(Plant).where(Plant.name == plant_name, Plant.is_simulated == 1))
    if plant is None:
        raise LookupError(f"No simulated plant named {plant_name}. Run the simulator first.")
    newest = session.scalar(
        select(func.max(Reading.device_time)).where(Reading.plant_id == plant.id)
    )
    if newest is None:
        raise LookupError(f"{plant_name} has no readings with a known time.")
    since = newest - timedelta(days=days)

    rows = session.scalars(
        select(Reading)
        .where(
            Reading.plant_id == plant.id,
            Reading.device_time.is_not(None),  # unknown times are left out (13.2)
            Reading.device_time > since,
        )
        .order_by(Reading.device_time)
    )
    readings = [
        {
            "t": _t(r.device_time),
            "moisture_pct": _num(r.moisture_pct),
            "lux": r.lux,
            "battery_mv": r.battery_mv,
            "time_status": r.time_status,
        }
        for r in rows
    ]
    gaps = [
        {"start": _t(g.gap_start), "end": _t(g.gap_end), "reason": "dropped"}
        for g in session.scalars(
            select(DataGap)
            .where(DataGap.plant_id == plant.id, DataGap.gap_end > since)
            .order_by(DataGap.gap_start)
        )
        if g.gap_start is not None and g.gap_end is not None
    ]
    events = [
        {
            "t": _t(e.device_time),
            "trigger": e.trigger_type,
            "duration_ms": e.duration_ms,
            "volume_ml": _num(e.volume_ml),
            "delivery": e.delivery,
            "moisture_before": _num(e.moisture_before),
        }
        for e in session.scalars(
            select(Event)
            .where(
                Event.plant_id == plant.id,
                Event.device_time.is_not(None),
                Event.device_time > since,
            )
            .order_by(Event.device_time)
        )
    ]
    return (
        {"plant_id": plant.id, "readings": readings, "gaps": gaps},
        {"plant_id": plant.id, "events": events},
    )


def write_mock_files(
    readings: dict, events: dict, out_dir: Path = MOCK_DIR, prefix: str = "sim-001"
):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = (out_dir / f"{prefix}-readings.json", out_dir / f"{prefix}-events.json")
    for path, body in zip(paths, (readings, events), strict=True):
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export SIM-001's last 14 days as mock JSON.")
    parser.add_argument("--out", type=Path, default=MOCK_DIR, help="Folder for the two files")
    args = parser.parse_args(argv)
    session = get_session()
    try:
        readings, events = export_plant(session)
    except LookupError as e:
        print(f"Export stopped: {e}", file=sys.stderr)
        return 1
    finally:
        session.close()
    for path in write_mock_files(readings, events, args.out):
        print(f"Wrote {path}")
    print(f"{len(readings['readings'])} readings, {len(events['events'])} waterings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
