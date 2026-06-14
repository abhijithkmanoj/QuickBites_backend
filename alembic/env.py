import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add backend root to path so app package imports work when Alembic runs.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.db.base import Base
from app.db.models import User  # noqa: F401
from app.core.config import settings

config = context.config
fileConfig(config.config_file_name)

configured_url = config.get_main_option("sqlalchemy.url")
if settings.DATABASE_URL:
    # Ensure Psycopg v3 driver is explicitly used (not psycopg2),
    # matching the logic in app/db/session.py
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    config.set_main_option("sqlalchemy.url", database_url)
elif configured_url is None:
    raise RuntimeError(
        "Alembic requires a database URL. Set DATABASE_URL in the environment or provide sqlalchemy.url in alembic.ini."
    )

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
