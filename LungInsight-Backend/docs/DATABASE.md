# DATABASE.md — LungInsight AI Backend Database Reference

PostgreSQL in production, SQLAlchemy 2.0 ORM, Alembic for migrations. The
test suite runs against SQLite automatically — see the "Cross-Dialect UUID
Type" section below for how that's made to work transparently.

## Entity-Relationship Overview

```
users (1) ──< uploaded_images (1) ──< predictions (1) ──< feedback
  │                                        │
  │                                        └──< feedback (also FK'd to user)
  ├──< chat_sessions (1) ──< chat_messages
  └──< logs (nullable FK — logs survive user deletion)

knowledge_sources  (standalone — no FK relationships; storage for the future RAG module)
```

## Tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| email | string(255) | unique, indexed |
| hashed_password | string(255) | bcrypt hash, never the plaintext |
| full_name | string(255) | nullable |
| is_active | boolean | default true; false = deactivated account, login blocked |
| created_at | timestamp | server default now() |
| updated_at | timestamp | auto-updates on row change |

### `uploaded_images`
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK -> users.id, `ON DELETE CASCADE` |
| original_filename | string(255) | client-supplied, display-only, never used as a disk path |
| stored_filename | string(255) | unique, server-generated (UUID + extension) |
| file_path | string(1024) | path on disk (or object storage key, if migrated later) |
| content_type | string(100) | validated against an allowlist at upload time |
| file_size_bytes | integer | actual streamed size, not client-declared |
| uploaded_at | timestamp | |

### `predictions`
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK -> users.id, `ON DELETE CASCADE` |
| image_id | UUID | FK -> uploaded_images.id, `ON DELETE CASCADE` |
| label | string(50) | `"Normal"` \| `"Pneumonia"` — populated by `InferenceClient`, not this backend |
| confidence | float | 0–100 |
| heatmap_path | string(1024) | nullable; path to a Grad-CAM PNG, populated by the AI module's output |
| created_at | timestamp | |

### `feedback`
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK -> users.id, `ON DELETE CASCADE` |
| prediction_id | UUID | FK -> predictions.id, `ON DELETE CASCADE` |
| rating | integer | 1–5, validated at the API layer |
| comment | text | nullable, max 2000 chars |
| created_at | timestamp | |

### `chat_sessions` / `chat_messages`
Storage layer for the (separately-built) chatbot module. `chat_sessions.user_id`
cascades on delete; `chat_messages.session_id` cascades from its parent session.
`chat_messages.role` is a free-text string (`"user"` / `"assistant"` / `"system"`)
rather than an enum, so the chat module can extend roles without a migration.

### `logs`
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK -> users.id, **`ON DELETE SET NULL`** — logs intentionally outlive user deletion |
| action | string(100) | e.g. `"login"`, `"register"`, `"logout"` |
| details | text | nullable, JSON-encoded extra context |
| ip_address | string(45) | nullable; sized for IPv6 |
| created_at | timestamp | |

### `knowledge_sources`
Standalone table for the future RAG/clinical-knowledge module — no foreign
keys, since it's not yet clear what will reference it. `source_type` is a
free-text string (`"pdf"` / `"url"` / `"text"`, etc.) for the same
extensibility reason as `chat_messages.role`.

## Cross-Dialect UUID Type

All primary/foreign keys use a custom `GUID` type (`app/db/types.py`)
instead of SQLAlchemy's PostgreSQL-only `UUID` type. In production
(PostgreSQL), it behaves exactly like the native `UUID` type. In tests
(SQLite), it transparently falls back to `CHAR(36)` string storage. This
means the exact same model definitions run unmodified against both
databases — the test suite needs no PostgreSQL instance at all.

## Migrations (Alembic)

```bash
# generate a new migration after changing models
alembic revision --autogenerate -m "describe the change"

# IMPORTANT: if the migration touches any GUID column (new table, new FK,
# etc.), autogenerate does NOT add the required import automatically.
# Open the generated file and add this line near the top if it's missing:
#     import app.db.types
# (Its absence causes a NameError at migration time, not at generation
# time — always test the migration with `alembic upgrade head` before
# committing it.)

# apply migrations
alembic upgrade head

# roll back one migration
alembic downgrade -1

# roll back everything
alembic downgrade base
```

`alembic/env.py` reads `DATABASE_URL` from the app's own settings
(`app.core.config.get_settings()`), so migrations always target whatever
database your `.env` currently points at — no separate migration-specific
connection string to keep in sync.

## Cascade Behavior Summary

| Relationship | On parent delete |
|---|---|
| user -> uploaded_images | CASCADE (delete user's images) |
| user -> predictions | CASCADE |
| user -> feedback | CASCADE |
| user -> chat_sessions | CASCADE |
| user -> logs | SET NULL (logs are retained for audit purposes) |
| uploaded_image -> predictions | CASCADE |
| prediction -> feedback | CASCADE |
| chat_session -> chat_messages | CASCADE |

## Indexes

- `users.email` — unique index, used on every login/register lookup
- All primary keys are indexed by default (UUID PKs)
- Consider adding a composite index on `(predictions.user_id, predictions.created_at)`
  if the `/history` and `/predictions` endpoints show slow query times at scale
  — not added preemptively here, since premature indexing has its own cost
  (slower writes) and the right index depends on real query patterns.
