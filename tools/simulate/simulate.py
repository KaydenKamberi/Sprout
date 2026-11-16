"""Launcher for app.simulator in server/ (spec 10.7 names the simulator tools/simulate).

Run from server/, so it uses the server's Python packages and DATABASE_URL:

    uv run python ../tools/simulate/simulate.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))

from app.simulator import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
