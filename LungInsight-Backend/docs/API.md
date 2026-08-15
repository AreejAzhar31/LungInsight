# API.md — LungInsight AI Backend API Reference

Interactive docs are always the source of truth (auto-generated from the
code, so they can't drift out of date): **`/docs`** (Swagger UI) or
**`/redoc`**. This file is a human-readable companion.

Base URL (local dev): `http://localhost:8000`

## Authentication

All endpoints except `/health`, `/register`, `/login`, and `/refresh`
require a Bearer token:

```
Authorization: Bearer <access_token>
```

Access tokens expire in 30 minutes (configurable); use `/api/v1/auth/refresh`
with your refresh token (7-day default expiry) to get a new pair without
re-authenticating with a password.

---

## `POST /api/v1/auth/register`

Create a new account. Rate limited to 5 requests/minute per IP.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "Jane Doe"
}
```
- `password`: 8–128 characters
- `full_name`: optional

**Response `201`:**
```json
{
  "user": {
    "id": "e1058831-7e7a-4f18-8258-7220f86adc3d",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "is_active": true,
    "created_at": "2026-08-02T09:15:30Z"
  },
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

**Errors:** `409` if the email is already registered, `422` for validation failures.

---

## `POST /api/v1/auth/login`

**Request body:**
```json
{ "email": "user@example.com", "password": "SecurePass123" }
```

**Response `200`:**
```json
{ "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }
```

**Errors:** `401` for wrong email/password, `403` if the account is deactivated.

---

## `POST /api/v1/auth/refresh`

**Request body:**
```json
{ "refresh_token": "eyJ..." }
```

**Response `200`:** same shape as login — a fresh access + refresh token pair.

**Errors:** `401` if the refresh token is invalid, expired, or is actually an access token.

---

## `POST /api/v1/auth/logout`

Requires auth. Since this backend uses stateless JWTs, this endpoint logs the
action server-side; the client is responsible for discarding its stored
tokens. (A token-blacklist table can be added later without changing this
endpoint's contract.)

**Response `200`:**
```json
{ "message": "Logged out successfully. Please discard your tokens client-side." }
```

---

## `POST /api/v1/prediction`

Requires auth. Uploads a chest X-ray image and creates a prediction record.

**Request:** `multipart/form-data` with a `file` field.
- Allowed types: `image/jpeg`, `image/png`, `image/jpg` (configurable via `ALLOWED_IMAGE_TYPES`)
- Max size: 10MB by default (configurable via `MAX_UPLOAD_SIZE_MB`)

**Response `201`:**
```json
{
  "id": "b2c3...",
  "image_id": "a1b2...",
  "label": "Pneumonia",
  "confidence": 87.5,
  "heatmap_path": null,
  "created_at": "2026-08-02T09:20:00Z"
}
```

**Note:** this backend does not run the AI model itself. The actual
`label`/`confidence`/`heatmap_path` values come from `InferenceClient`
(currently a stub — see `app/services/inference_client.py`); wire in the
real model-serving call there.

**Errors:** `422` for an invalid/oversized file, `401` if not authenticated.

---

## `GET /api/v1/prediction/{id}`

Requires auth. Returns a single prediction — only if it belongs to the
authenticated user (otherwise `404`, not `403`, to avoid leaking existence).

**Response `200`:** same shape as the create-prediction response.

---

## `GET /api/v1/predictions`

Requires auth. Paginated list of the current user's predictions, newest first.

**Query params:** `page` (default 1), `page_size` (default 20, max 100)

**Response `200`:**
```json
{
  "items": [ /* PredictionResponse[] */ ],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

---

## `GET /api/v1/history`

Requires auth. Like `/predictions`, but each item includes the source
image's original filename (joined from `uploaded_images`).

**Query params:** `page`, `page_size` (same as above)

**Response `200`:**
```json
{
  "items": [
    {
      "prediction_id": "b2c3...",
      "image_filename": "xray.jpg",
      "label": "Pneumonia",
      "confidence": 87.5,
      "heatmap_path": null,
      "created_at": "2026-08-02T09:20:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## `POST /api/v1/feedback`

Requires auth. Leave feedback on one of your own predictions.

**Request body:**
```json
{ "prediction_id": "b2c3...", "rating": 4, "comment": "Looks about right" }
```
- `rating`: integer 1–5
- `comment`: optional, max 2000 characters

**Response `201`:**
```json
{
  "id": "f4e5...",
  "prediction_id": "b2c3...",
  "rating": 4,
  "comment": "Looks about right",
  "created_at": "2026-08-02T09:25:00Z"
}
```

**Errors:** `404` if the prediction doesn't exist *or* belongs to another
user (feedback can only be left on your own predictions).

---

## `GET /health`

No auth required. Used by uptime monitors / load balancers / container
orchestrators.

**Response `200`:**
```json
{ "status": "ok", "app_name": "LungInsight AI Backend", "database": "connected" }
```

`database` will read `"unavailable"` (not a 500 error) if the DB connection
check fails, so the endpoint itself stays reliable for liveness probes even
during a DB outage.

---

## Error Response Shape

All application errors (not raw FastAPI validation errors) follow this shape:

```json
{ "detail": "Human-readable error message." }
```

| Status | Meaning |
|---|---|
| 401 | Missing/invalid/expired token, or wrong credentials |
| 403 | Account deactivated |
| 404 | Resource not found (or not owned by the current user) |
| 409 | Email already registered |
| 422 | Validation failure (request body or file) |
| 429 | Rate limit exceeded |
