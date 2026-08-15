"""API tests for /api/v1/prediction* endpoints."""
import io
import uuid


def _upload(client, headers, filename="xray.jpg", content_type="image/jpeg", content=b"\xff\xd8fakejpeg"):
    return client.post(
        "/api/v1/prediction",
        headers=headers,
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


def test_create_prediction_requires_auth(client):
    r = client.post("/api/v1/prediction", files={"file": ("x.jpg", io.BytesIO(b"data"), "image/jpeg")})
    assert r.status_code == 401


def test_create_prediction_success(client, auth_headers):
    r = _upload(client, auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["label"] in ("Normal", "Pneumonia")
    assert 0 <= body["confidence"] <= 100


def test_create_prediction_rejects_invalid_file_type(client, auth_headers):
    r = _upload(client, auth_headers, filename="doc.txt", content_type="text/plain")
    assert r.status_code == 422


def test_get_prediction_by_id(client, auth_headers):
    created = _upload(client, auth_headers).json()
    r = client.get(f"/api/v1/prediction/{created['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_prediction_not_found_returns_404(client, auth_headers):
    r = client.get(f"/api/v1/prediction/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404


def test_get_prediction_requires_auth(client, auth_headers):
    created = _upload(client, auth_headers).json()
    r = client.get(f"/api/v1/prediction/{created['id']}")
    assert r.status_code == 401


def test_list_predictions_returns_only_own(client, auth_headers, db_session):
    _upload(client, auth_headers)
    _upload(client, auth_headers)

    r = client.get("/api/v1/predictions", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_list_predictions_pagination_params(client, auth_headers):
    for _ in range(3):
        _upload(client, auth_headers)

    r = client.get("/api/v1/predictions?page=1&page_size=2", headers=auth_headers)
    body = r.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3


def test_predictions_are_isolated_between_users(client):
    # user A
    r = client.post("/api/v1/auth/register", json={"email": "userA@example.com", "password": "SecurePass123"})
    headers_a = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    _upload(client, headers_a)

    # user B
    r = client.post("/api/v1/auth/register", json={"email": "userB@example.com", "password": "SecurePass123"})
    headers_b = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}

    r = client.get("/api/v1/predictions", headers=headers_b)
    assert r.json()["total"] == 0  # user B sees none of user A's predictions
