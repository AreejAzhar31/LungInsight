"""
Shared pytest fixtures.

Each test gets a fresh, isolated in-memory SQLite database (fast, no
external dependencies) via dependency override of `get_db` — the app code
itself is completely unaware it's not talking to PostgreSQL, since both
are accessed through the same SQLAlchemy session interface.
"""

from __future__ import annotations
import os

# Tests must never depend on whatever happens to be in the local .env file,
# or on the AI/RAG microservices actually running. Several modules read
# settings at import time (main.py, health.py, auth.py, etc.), so these
# overrides must happen here, before any app.* import below -- setting them
# inside a fixture would run too late, after those modules already cached
# whatever was in the real .env (e.g. INFERENCE_MODE=http from a live demo
# session), causing the whole suite to attempt real network calls and fail
# with 503s. This guarantees the suite always runs fully offline.
os.environ["INFERENCE_MODE"] = "stub"
os.environ["RAG_MODE"] = "stub"
os.environ["STORAGE_MODE"] = "local"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
import app.models  # noqa: F401 -- registers all models
from app.main import app
from app.middleware.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """
    slowapi's in-memory limit storage persists across tests within the same
    process. Without resetting it, tests that register multiple users (each
    hitting the 5/minute auth rate limit) start failing with 429s purely due
    to test ordering/count, not real rate-limit behavior under test.
    """
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user_tokens(client):
    """Registers a user and returns (email, password, access_token, refresh_token)."""
    email = "fixture_user@example.com"
    password = "SecurePass123"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Fixture User"})
    assert r.status_code == 201
    tokens = r.json()["tokens"]
    return {
        "email": email,
        "password": password,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


@pytest.fixture()
def auth_headers(registered_user_tokens):
    return {"Authorization": f"Bearer {registered_user_tokens['access_token']}"}
