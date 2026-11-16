"""B1: the species loader and the seeded account (spec 9.3, 3.6)."""

from decimal import Decimal

import pytest
from argon2 import PasswordHasher
from sqlalchemy import func, select

from app.models import Account, Species
from app.seed import (
    CSV_COLUMNS,
    SPECIES_CSV,
    SeedError,
    ensure_seed_account,
    load_species,
    read_species_csv,
)

HEADER = ",".join(CSV_COLUMNS)
BASIL = "Basil,Ocimum basilicum,4.0,6.0,30.0,false,false,https://example.edu/basil"
MINT = "Mint,Mentha spicata,3.0,5.0,35.0,true,1,https://example.edu/mint"
FERN = "Fern,Nephrolepis exaltata,5.5,3.0,40.0,,0,https://example.edu/fern"


def write_csv(tmp_path, *lines, name="species.csv"):
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def species_count(session):
    return session.scalar(select(func.count()).select_from(Species))


def test_loader_loads_every_row(db_session, tmp_path):
    path = write_csv(tmp_path, HEADER, BASIL, MINT, FERN)
    assert load_species(db_session, path) == 3
    assert species_count(db_session) == 3
    mint = db_session.scalar(select(Species).where(Species.common_name == "Mint"))
    assert mint.scientific_name == "Mentha spicata"
    assert mint.days_between_waterings == Decimal("3.0")
    assert mint.light_hours == Decimal("5.0")
    assert mint.water_threshold_pct == Decimal("35.0")
    assert (mint.toxic_to_cats, mint.toxic_to_dogs) == (1, 1)
    assert mint.source_url == "https://example.edu/mint"
    fern = db_session.scalar(select(Species).where(Species.common_name == "Fern"))
    assert (fern.toxic_to_cats, fern.toxic_to_dogs) == (None, 0)


def test_loading_the_same_file_twice_adds_no_duplicates(db_session, tmp_path):
    path = write_csv(tmp_path, HEADER, BASIL, MINT)
    assert load_species(db_session, path) == 2
    assert load_species(db_session, path) == 0
    assert species_count(db_session) == 2


def test_the_repo_csv_loads(db_session):
    # Until Design delivers D1, the repo CSV holds one clearly marked test row.
    rows = read_species_csv(SPECIES_CSV)
    assert len(rows) >= 1
    assert load_species(db_session, SPECIES_CSV) == len(rows)


def test_missing_column_is_refused_with_a_clear_error(db_session, tmp_path):
    header = ",".join(c for c in CSV_COLUMNS if c != "source_url")
    path = write_csv(tmp_path, header, "Basil,Ocimum basilicum,4.0,6.0,30.0,false,false")
    with pytest.raises(SeedError, match="Missing: source_url"):
        load_species(db_session, path)
    assert species_count(db_session) == 0


def test_extra_column_is_refused(db_session, tmp_path):
    path = write_csv(tmp_path, HEADER + ",notes", BASIL + ",tasty")
    with pytest.raises(SeedError, match="Extra: notes"):
        load_species(db_session, path)


def test_bad_values_are_refused(db_session, tmp_path):
    bad_number = BASIL.replace("4.0", "four")
    with pytest.raises(SeedError, match="days_between_waterings must be a number"):
        load_species(db_session, write_csv(tmp_path, HEADER, bad_number, name="a.csv"))
    bad_flag = BASIL.replace("false,false", "maybe,false")
    with pytest.raises(SeedError, match="toxic_to_cats must be"):
        load_species(db_session, write_csv(tmp_path, HEADER, bad_flag, name="b.csv"))


def test_seeded_account(db_session, monkeypatch):
    monkeypatch.setenv("SEED_ACCOUNT_PASSWORD", "throwaway-test-password")
    assert ensure_seed_account(db_session) is True
    account = db_session.get(Account, 1)
    assert account.email == "dev@sprout.local"
    assert account.password_hash != "throwaway-test-password"
    assert PasswordHasher().verify(account.password_hash, "throwaway-test-password")
    # A second run leaves the existing account alone.
    assert ensure_seed_account(db_session) is False


def test_seed_stops_without_the_password(db_session, monkeypatch):
    monkeypatch.delenv("SEED_ACCOUNT_PASSWORD", raising=False)
    with pytest.raises(SeedError, match="SEED_ACCOUNT_PASSWORD is not set"):
        ensure_seed_account(db_session)
    assert db_session.get(Account, 1) is None
