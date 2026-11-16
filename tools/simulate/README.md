# The simulator

Makes eight weeks of fake, messy plant data for three simulated plants (SIM-001, SIM-002,
SIM-003), so the backend and the dashboard can be built before a real plant exists
(spec 3.2, 10.7, task card B2). The data goes through `ingest_batch`, the same path a real
stake's upload takes.

**Only ever run it against a development database.** Never point it at the live database
(spec 5.2). It refuses to run if the database already holds a real (non-simulated) plant.

## Run it

From the `server/` folder, with `DATABASE_URL` set (see `.env.example`):

1. Create the tables: `uv run alembic upgrade head`
2. Load the species and the seeded account: `uv run python -m app.seed`
3. Run the simulator: `uv run python ../tools/simulate/simulate.py --end 2026-11-16`
4. Export SIM-001's last 14 days for the dashboard's mock data:
   `uv run python ../tools/simulate/export_mock.py`

- `--end` is the UTC date the eight weeks end on. Leave it out to end today. The same date
  always gives the same data (random seed 42).
- The simulator writes `sim_truth.json`, the true drying rates, to `tools/simulate/output/`.
  That folder isn't committed.
- The export writes `web/src/api/mock/sim-001-readings.json` and
  `web/src/api/mock/sim-001-events.json`, in the exact shapes of
  `GET /api/plants/:id/readings?days=14` and `GET /api/plants/:id/events?days=14` (spec 13.2).

If you're more comfortable without the terminal, ask Claude in the desktop app to run these
steps for you.

## What's in the data

- **Three plants**, each on its own simulated stake:
  - SIM-001 on SPROUT-901 and SIM-002 on SPROUT-902 dry in straight lines.
  - SIM-003 on SPROUT-903 dries in a curve.
- **Hourly readings for eight weeks.** They're uploaded once each weekday between 11:30 and
  12:40 (Los Angeles time), and never at weekends. So weekend readings arrive "estimated"
  and the server re-dates them.
- **The mess from spec 10.7:**
  - 2% of readings dropped;
  - one 14-hour network outage;
  - one manual watering;
  - a run of 6 sensor-fault readings;
  - one day of zero light;
  - one recalibration halfway through.

`sim-001-moisture.png` shows SIM-001's moisture over the eight weeks.
