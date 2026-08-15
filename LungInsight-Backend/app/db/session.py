"""
Database engine and session management.

Uses SQLAlchemy's synchronous engine/session for simplicity and broad
compatibility (works identically against PostgreSQL in production and
SQLite in tests). A `get_db` dependency yields a session per-request and
guarantees it's closed afterward.
"""

from __future__ import annotations
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

settings = get_settings()

# `connect_args` only applies to SQLite (used in tests); ignored by Postgres.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session, closes it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
