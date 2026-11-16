"""Alembic migration runner.

The database address always comes from the DATABASE_URL environment variable, never from
alembic.ini, so no address or password is ever committed. There are no migrations yet:
checkpoint B1 creates every table in spec section 9.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# B1 replaces this with the models' MetaData so autogenerate can compare tables.
target_metadata = None


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. See .env.example at the repo root.")
    return url


def run_migrations_offline() -> None:
    """Write the migration SQL to the screen instead of running it."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to MySQL and run the migrations."""
    connectable = create_engine(database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
