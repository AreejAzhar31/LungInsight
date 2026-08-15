# LungInsight AI — Backend

Production-ready backend for LungInsight AI: authentication, prediction
storage, history, and feedback. Built with FastAPI, PostgreSQL,
SQLAlchemy, and Alembic.

**Scope note:** this module does **not** run the AI model, GradCAM, chatbot,
or RAG pipeline. Those are separate modules. This backend defines a
pluggable `InferenceClient` interface (see `app/services/inference_client.py`)
as the integration point — swap the stub implementation for a real call to
the model-serving module when it's ready.

## Quick Start

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env
# edit .env: set DATABASE_URL to your PostgreSQL instance, and a real JWT_SECRET_KEY

alembic upgrade head

uvicorn app.main:app --reload
```

API docs (Swagger UI): http://localhost:8000/docs
Alternative docs (ReDoc): http://localhost:8000/redoc
Health check: http://localhost:8000/health

## Architecture

Clean Architecture with four layers, each only depending on the layer below it:

```
Routers (app/api/routers/)       <- HTTP request/response, no business logic
      |
Services (app/services/)          <- business logic, orchestrates repositories
      |
Repositories (app/repositories/)  <- data access, the ONLY layer touching the DB session
      |
Models (app/models/)              <- SQLAlchemy ORM table definitions
```

Dependency injection wires all of this together in `app/api/dependencies.py`
— routers only ever depend on services, obtained via `Depends()`.

## Project Structure

```
app/
  api/
    routers/          # auth, predictions, history, feedback, health
    dependencies.py   # DI wiring + current-user auth dependency
  core/
    config.py          # environment-variable-driven settings
    security.py        # password hashing (bcrypt), JWT tokens
    exceptions.py       # custom exceptions -> HTTP status mapping
  db/
    base.py            # SQLAlchemy declarative base
    session.py          # engine + session factory
    types.py            # cross-dialect UUID column type
  models/               # ORM models (one file per table/group)
  schemas/              # Pydantic request/response DTOs
  repositories/          # data access layer
  services/               # business logic layer
  middleware/
    rate_limit.py          # slowapi rate limiter config
  main.py                   # FastAPI app assembly
alembic/                     # database migrations
tests/
  unit/                      # pure logic, no DB/HTTP
  integration/                 # service + repository + DB (SQLite)
  api/                          # full HTTP request/response cycle
docs/
  API.md
  DATABASE.md
```

## Security Features

- **JWT authentication** — short-lived access tokens (30 min default) + longer-lived refresh tokens (7 days default)
- **bcrypt password hashing** — via the `bcrypt` library directly (not `passlib`, to sidestep a known `passlib`/`bcrypt` 4.x compatibility bug)
- **Rate limiting** — via `slowapi`, tighter limits on auth endpoints (5/min default) than general API calls (100/min default)
- **Input validation** — Pydantic schemas validate every request body (email format, password length, rating ranges, etc.)
- **File validation** — content-type allowlist + streamed size-limit enforcement (never trusts client-declared file size), random server-generated filenames (never trusts client filenames)
- **CORS** — configurable allowed origins via environment variable
- **Environment variables** — all secrets/config loaded via `pydantic-settings`, nothing hardcoded

## Running Tests

```bash
pytest tests/ -v
```

56 tests across three layers:
- `tests/unit/` — password hashing, JWT tokens, file validation (no DB)
- `tests/integration/` — services against a real (in-memory SQLite) DB session
- `tests/api/` — full HTTP flows through FastAPI's TestClient, including auth isolation between users

Tests run against SQLite automatically (no PostgreSQL required for the test suite) — see `tests/conftest.py`.

## Further Documentation

- [`docs/API.md`](docs/API.md) — full endpoint reference
- [`docs/DATABASE.md`](docs/DATABASE.md) — schema, relationships, migrations
