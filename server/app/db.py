"""The database engine and sessions, built from the DATABASE_URL environment variable.

Ordinary (not async) SQLAlchemy sessions. MySQL 8.4 only (spec 9). Never point a
development app or a test at the live database (spec 5.2).
"""

import os
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. See .env.example at the repo root.")
    return url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True)


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Session:
    """A new database session. The caller commits or rolls back, then closes it."""
    return _session_factory()()
