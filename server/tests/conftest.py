"""Shared test fixtures for every backend card.

- At the start of the test session, the database at DATABASE_URL is migrated to the
  latest schema (alembic upgrade head).
- Each test gets a database session (the db_session fixture), and every table is emptied
  after it, so tests don't affect each other.

Safety (spec 5.2: never point tests at the live database): emptying tables deletes data,
so the tests refuse to start on a database that already holds rows. They only ever empty
data they created themselves.
"""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.db import get_engine, get_session

SERVER_DIR = Path(__file__).resolve().parents[1]


def alembic_config() -> Config:
    return Config(str(SERVER_DIR / "alembic.ini"))


def app_tables(conn) -> list[str]:
    """Every table in the current database except Alembic's own bookkeeping table."""
    rows = conn.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name <> 'alembic_version'"
        )
    )
    return [r[0] for r in rows]


def empty_all_tables() -> None:
    with get_engine().begin() as conn:
        tables = app_tables(conn)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        try:
            for table in tables:
                conn.execute(text(f"TRUNCATE TABLE `{table}`"))
        finally:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    if not os.environ.get("DATABASE_URL"):
        pytest.exit(
            "DATABASE_URL is not set. Tests need a MySQL 8.4 test database "
            "(GitHub Actions provides one; locally, see .env.example).",
            returncode=1,
        )
    command.upgrade(alembic_config(), "head")
    with get_engine().connect() as conn:
        holding_rows = [
            t
            for t in app_tables(conn)
            if conn.execute(text(f"SELECT 1 FROM `{t}` LIMIT 1")).first()
        ]
    if holding_rows:
        pytest.exit(
            "Refusing to run: the database at DATABASE_URL already holds data in "
            f"{', '.join(sorted(holding_rows))}. Tests empty every table, so they only run "
            "on an empty test database, never on a database with real or development data.",
            returncode=1,
        )
    yield


@pytest.fixture
def db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        empty_all_tables()
