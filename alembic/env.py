"""Alembic environment configuration.

Uses SQLAlchemy async engine so it works with the same asyncpg driver
used by the rest of the application. The DATABASE_URL is read from .env
and the asyncpg-incompatible query params (sslmode, channel_binding) are
stripped by the same helper used in db/session.py.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_engine_from_config

from db.models import Base
from db.session import _prepare_url

load_dotenv()

# Alembic config object — gives access to values in alembic.ini.
config = context.config

# Set up Python loggers from the [loggers] section in alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object that autogenerate inspects to detect schema changes.
target_metadata = Base.metadata


def _get_url() -> str:
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        raise RuntimeError("DATABASE_URL is not set in .env")
    clean_url, _ = _prepare_url(raw)
    return clean_url


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL to stdout)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[type-arg]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using the async engine."""
    raw_url = os.environ.get("DATABASE_URL", "")
    clean_url, connect_args = _prepare_url(raw_url)

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = clean_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection (default mode)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
