"""API tests for /api/v1/history, /api/v1/feedback, and /health."""
import io
import uuid


def _upload(client, headers):
    r = client.post(
        "/api/v1/prediction",
        headers=headers,
        files={"file": ("xray.jpg", io.BytesIO(b"\xff\xd8fakejpeg"), "image/jpeg")},
    )
    return r.json()


# ---- health --------------------------------------------------

def test_health_check_no_auth_required(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    # Default INFERENCE_MODE/RAG_MODE is "stub" in tests, so both
    # dependency probes should report "stub" rather than attempting a
    # real network call to a service that isn't running.
    assert body["inference_service"] == "stub"
    assert body["rag_service"] == "stub"


# ---- history --------------------------------------------------

def test_history_requires_auth(client):
    r = client.get("/api/v1/history")
    assert r.status_code == 401


def test_history_returns_predictions_with_filenames(client, auth_headers):
    _upload(client, auth_headers)
    r = client.get("/api/v1/history", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["image_filename"] == "xray.jpg"
    assert body["items"][0]["label"] in ("Normal", "Pneumonia")


def test_history_empty_for_new_user(client, auth_headers):
    r = client.get("/api/v1/history", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ---- feedback --------------------------------------------------

def test_feedback_requires_auth(client):
    r = client.post("/api/v1/feedback", json={"prediction_id": str(uuid.uuid4()), "rating": 5})
    assert r.status_code == 401


def test_feedback_success(client, auth_headers):
    prediction = _upload(client, auth_headers)
    r = client.post(
        "/api/v1/feedback",
        headers=auth_headers,
        json={"prediction_id": prediction["id"], "rating": 4, "comment": "Reasonable"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["rating"] == 4
    assert body["comment"] == "Reasonable"


def test_feedback_invalid_rating_rejected(client, auth_headers):
    prediction = _upload(client, auth_headers)
    r = client.post(
        "/api/v1/feedback",
        headers=auth_headers,
        json={"prediction_id": prediction["id"], "rating": 10},  # out of 1-5 range
    )
    assert r.status_code == 422


def test_feedback_on_nonexistent_prediction_returns_404(client, auth_headers):
    r = client.post(
        "/api/v1/feedback",
        headers=auth_headers,
        json={"prediction_id": str(uuid.uuid4()), "rating": 3},
    )
    assert r.status_code == 404


def test_feedback_on_another_users_prediction_returns_404(client):
    r = client.post("/api/v1/auth/register", json={"email": "fbUserA@example.com", "password": "SecurePass123"})
    headers_a = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    prediction = _upload(client, headers_a)

    r = client.post("/api/v1/auth/register", json={"email": "fbUserB@example.com", "password": "SecurePass123"})
    headers_b = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}

    r = client.post(
        "/api/v1/feedback",
        headers=headers_b,
        json={"prediction_id": prediction["id"], "rating": 3},
    )
    assert r.status_code == 404  # can't leave feedback on someone else's prediction
