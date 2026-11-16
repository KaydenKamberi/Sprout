"""Placeholder test: proves the server can reach MySQL 8.4 through DATABASE_URL."""

import os

import pytest
from sqlalchemy import create_engine, text


def test_mysql_answers_select_1():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.fail(
            "DATABASE_URL is not set. Start MySQL with docker compose and set DATABASE_URL "
            "as shown in .env.example."
        )
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        engine.dispose()
