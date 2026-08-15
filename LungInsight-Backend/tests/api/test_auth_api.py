"""API tests for /api/v1/auth/* endpoints — full HTTP request/response cycle."""


def test_register_success(client):
    r = client.post("/api/v1/auth/register", json={"email": "new@example.com", "password": "SecurePass123"})
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "new@example.com"
    assert "access_token" in body["tokens"]
    assert "refresh_token" in body["tokens"]


def test_register_weak_password_rejected(client):
    r = client.post("/api/v1/auth/register", json={"email": "weak@example.com", "password": "short"})
    assert r.status_code == 422  # pydantic min_length validation


def test_register_invalid_email_rejected(client):
    r = client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "SecurePass123"})
    assert r.status_code == 422


def test_register_duplicate_email_returns_409(client, registered_user_tokens):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": registered_user_tokens["email"], "password": "AnotherPass456"},
    )
    assert r.status_code == 409


def test_login_success(client, registered_user_tokens):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user_tokens["email"], "password": registered_user_tokens["password"]},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_returns_401(client, registered_user_tokens):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user_tokens["email"], "password": "WrongPassword999"},
    )
    assert r.status_code == 401


def test_refresh_success(client, registered_user_tokens):
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": registered_user_tokens["refresh_token"]})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_refresh_with_garbage_token_returns_401(client):
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert r.status_code == 401


def test_logout_requires_auth(client):
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 401


def test_logout_success(client, auth_headers):
    r = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert r.status_code == 200


def test_get_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_get_me_returns_current_user(client, auth_headers, registered_user_tokens):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == registered_user_tokens["email"]
    assert "id" in body and "created_at" in body


def test_update_me_requires_auth(client):
    r = client.patch("/api/v1/auth/me", json={"full_name": "New Name"})
    assert r.status_code == 401


def test_update_me_persists_full_name(client, auth_headers):
    r = client.patch("/api/v1/auth/me", headers=auth_headers, json={"full_name": "Jane Clinician"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Jane Clinician"

    # Confirm it actually persisted, not just echoed back in the response.
    r2 = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r2.json()["full_name"] == "Jane Clinician"


def test_update_me_with_blank_name_clears_it(client, auth_headers):
    client.patch("/api/v1/auth/me", headers=auth_headers, json={"full_name": "Someone"})
    r = client.patch("/api/v1/auth/me", headers=auth_headers, json={"full_name": "   "})
    assert r.status_code == 200
    assert r.json()["full_name"] is None
