"""Load the species CSV (D1) and insert the seeded account (spec 9.3, 3.6).

Run it after the migrations (spec 15.4 step 5), from server/:

    uv run python -m app.seed

It needs DATABASE_URL and SEED_ACCOUNT_PASSWORD in the environment. The password is
never stored or printed; only its argon2 hash goes into accounts.password_hash.
"""

import csv
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Account, Species

SPECIES_CSV = Path(__file__).resolve().parent.parent / "seed" / "species.csv"

# The eight columns D1 delivers, in this order (spec 9.3).
CSV_COLUMNS = [
    "common_name",
    "scientific_name",
    "days_between_waterings",
    "light_hours",
    "water_threshold_pct",
    "toxic_to_cats",
    "toxic_to_dogs",
    "source_url",
]

SEED_ACCOUNT_ID = 1
SEED_ACCOUNT_EMAIL = "dev@sprout.local"
SEED_PASSWORD_VAR = "SEED_ACCOUNT_PASSWORD"


class SeedError(Exception):
    """The seed can't run: a bad CSV or a missing setting. The message says what to fix."""


def _decimal(value: str, column: str, line: int) -> Decimal:
    try:
        return Decimal(value.strip())
    except InvalidOperation:
        raise SeedError(f"Line {line}: {column} must be a number, got {value!r}.") from None


def _flag(value: str, column: str, line: int) -> int | None:
    # Open question (task card B1, section 9, question 4): how D1 writes true/false.
    # Until it's answered, accept true/false, 1/0, and blank (unknown, stored as NULL).
    v = value.strip().lower()
    if v in ("true", "1"):
        return 1
    if v in ("false", "0"):
        return 0
    if v == "":
        return None
    raise SeedError(f"Line {line}: {column} must be true, false, 1, 0 or blank, got {value!r}.")


def read_species_csv(path: Path) -> list[dict]:
    """Read and check the CSV. Every row becomes a dict of species column values."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise SeedError(f"{path} is empty; it needs a header row.")
        header = [h.strip() for h in header]
        if header != CSV_COLUMNS:
            missing = [c for c in CSV_COLUMNS if c not in header]
            extra = [c for c in header if c not in CSV_COLUMNS]
            raise SeedError(
                f"{path} has the wrong columns. Expected, in order: {', '.join(CSV_COLUMNS)}. "
                f"Missing: {', '.join(missing) or 'none'}. Extra: {', '.join(extra) or 'none'}."
            )
        rows = []
        for line, cells in enumerate(reader, start=2):
            if not any(c.strip() for c in cells):
                continue
            if len(cells) != len(CSV_COLUMNS):
                raise SeedError(
                    f"Line {line}: expected {len(CSV_COLUMNS)} values, got {len(cells)}."
                )
            r = dict(zip(CSV_COLUMNS, cells, strict=True))
            for text_col in ("common_name", "scientific_name", "source_url"):
                if not r[text_col].strip():
                    raise SeedError(f"Line {line}: {text_col} is empty.")
            rows.append(
                {
                    "common_name": r["common_name"].strip(),
                    "scientific_name": r["scientific_name"].strip(),
                    "days_between_waterings": _decimal(
                        r["days_between_waterings"], "days_between_waterings", line
                    ),
                    "light_hours": _decimal(r["light_hours"], "light_hours", line),
                    "water_threshold_pct": _decimal(
                        r["water_threshold_pct"], "water_threshold_pct", line
                    ),
                    "toxic_to_cats": _flag(r["toxic_to_cats"], "toxic_to_cats", line),
                    "toxic_to_dogs": _flag(r["toxic_to_dogs"], "toxic_to_dogs", line),
                    "source_url": r["source_url"].strip(),
                }
            )
    return rows


def load_species(session: Session, path: Path = SPECIES_CSV) -> int:
    """Insert the CSV's species. Returns how many rows were new.

    Open question (task card B1, section 9, question 2): which column identifies a
    species that's already loaded. Until it's answered, a row is skipped only when a
    species with exactly the same eight values already exists, so loading the same file
    twice adds nothing, and no row is ever overwritten.
    """
    added = 0
    for row in read_species_csv(path):
        same_values = [
            getattr(Species, column).is_(None)
            if value is None
            else getattr(Species, column) == value
            for column, value in row.items()
        ]
        existing = session.scalar(select(Species.id).where(*same_values))
        if existing is None:
            session.add(Species(**row))
            added += 1
    session.flush()
    return added


def ensure_seed_account(session: Session) -> bool:
    """Insert account id 1 (dev@sprout.local) if it doesn't exist. Returns True if added."""
    if session.get(Account, SEED_ACCOUNT_ID) is not None:
        return False
    password = os.environ.get(SEED_PASSWORD_VAR)
    if not password:
        raise SeedError(
            f"{SEED_PASSWORD_VAR} is not set. Add it to your .env (see .env.example); "
            "the seeded account's password is read from it and never stored in plain text."
        )
    session.add(
        Account(
            id=SEED_ACCOUNT_ID,
            email=SEED_ACCOUNT_EMAIL,
            password_hash=PasswordHasher().hash(password),
        )
    )
    session.flush()
    return True


def main() -> int:
    session = get_session()
    try:
        account_added = ensure_seed_account(session)
        species_added = load_species(session)
        session.commit()
    except SeedError as e:
        session.rollback()
        print(f"Seed stopped: {e}", file=sys.stderr)
        return 1
    finally:
        session.close()
    print(f"Seeded account: {'added' if account_added else 'already there'}.")
    print(f"Species: {species_added} new row(s) from {SPECIES_CSV.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
