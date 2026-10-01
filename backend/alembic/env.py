"""Alembic environment using the project's synchronous database engine."""

from sqlalchemy import pool
from sqlalchemy.engine import Connection, create_engine

import app.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.database.base import Base

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without opening a database connection."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured to run Alembic migrations.")

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a synchronous SQLAlchemy connection."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured to run Alembic migrations.")

    connectable = create_engine(settings.database_url, poolclass=pool.NullPool)
    try:
        with connectable.connect() as connection:
            do_run_migrations(connection)
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
