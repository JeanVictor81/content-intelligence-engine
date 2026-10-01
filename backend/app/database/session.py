"""Synchronous PostgreSQL engine and session dependency."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create and cache the application database engine."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured before accessing the database.")
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_db() -> Iterator[Session]:
    """Yield a short-lived synchronous SQLAlchemy session."""
    with Session(get_engine()) as session:
        yield session
