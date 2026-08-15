"""API tests for /api/v1/chat* endpoints (uses StubRagClient — RAG_MODE=stub by default)."""
import io
import uuid


def _upload_prediction(client, headers):
    r = client.post(
        "/api/v1/prediction",
        headers=headers,
        files={"file": ("xray.jpg", io.BytesIO(b"\xff\xd8fakejpeg"), "image/jpeg")},
    )
    assert r.status_code == 201
    return r.json()


def test_start_session_requires_auth(client):
    r = client.post("/api/v1/chat/sessions", json={})
    assert r.status_code == 401


def test_start_session_without_prediction(client, auth_headers):
    r = client.post("/api/v1/chat/sessions", headers=auth_headers, json={})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] is None
    assert body["prediction_id"] is None


def test_start_session_with_prediction_sets_title(client, auth_headers):
    prediction = _upload_prediction(client, auth_headers)
    r = client.post(
        "/api/v1/chat/sessions", headers=auth_headers, json={"prediction_id": prediction["id"]}
    )
    assert r.status_code == 201
    body = r.json()
    assert prediction["label"] in body["title"]
    assert body["prediction_id"] == prediction["id"]


def test_prediction_id_persists_across_reload(client, auth_headers):
    """The exact scenario this was built for: linked prediction survives
    listing sessions again later, not just in the immediate response."""
    prediction = _upload_prediction(client, auth_headers)
    session = client.post(
        "/api/v1/chat/sessions", headers=auth_headers, json={"prediction_id": prediction["id"]}
    ).json()

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers).json()
    reloaded = next(s for s in sessions if s["id"] == session["id"])
    assert reloaded["prediction_id"] == prediction["id"]


def test_sending_message_without_resending_prediction_id_stays_grounded(client, auth_headers):
    """Once a session is linked to a prediction, later messages don't need
    to resend prediction_id -- the stored one is used automatically."""
    prediction = _upload_prediction(client, auth_headers)
    session = client.post(
        "/api/v1/chat/sessions", headers=auth_headers, json={"prediction_id": prediction["id"]}
    ).json()

    # No prediction_id in this request -- service should fall back to the
    # session's own stored one rather than sending ungrounded context.
    r = client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json={"message": "What does this mean?"},
    )
    assert r.status_code == 200


def test_start_session_with_unknown_prediction_returns_404(client, auth_headers):
    r = client.post(
        "/api/v1/chat/sessions", headers=auth_headers, json={"prediction_id": str(uuid.uuid4())}
    )
    assert r.status_code == 404


def test_send_message_persists_and_returns_stub_answer(client, auth_headers):
    session = client.post("/api/v1/chat/sessions", headers=auth_headers, json={}).json()

    r = client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json={"message": "What does this mean?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == session["id"]
    assert isinstance(body["answer"], str) and len(body["answer"]) > 0
    assert body["is_safe"] is True

    history = client.get(
        f"/api/v1/chat/sessions/{session['id']}/messages", headers=auth_headers
    ).json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_send_message_to_other_users_session_returns_404(client, auth_headers):
    session = client.post("/api/v1/chat/sessions", headers=auth_headers, json={}).json()

    other = client.post(
        "/api/v1/auth/register",
        json={"email": "other_chat_user@example.com", "password": "SecurePass123"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['tokens']['access_token']}"}

    r = client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        headers=other_headers,
        json={"message": "hi"},
    )
    assert r.status_code == 404


def test_send_message_auto_titles_untitled_session(client, auth_headers):
    session = client.post("/api/v1/chat/sessions", headers=auth_headers, json={}).json()
    assert session["title"] is None

    client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json={"message": "What is pneumonia and how is it treated?"},
    )

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers).json()
    reloaded = next(s for s in sessions if s["id"] == session["id"])
    assert reloaded["title"] == "What is pneumonia and how is it treated?"


def test_auto_title_truncates_long_first_message(client, auth_headers):
    session = client.post("/api/v1/chat/sessions", headers=auth_headers, json={}).json()

    long_message = "Can you please explain in a lot of detail what pneumonia is, how it develops, and what foods or lifestyle changes might help recovery"
    client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json={"message": long_message},
    )

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers).json()
    reloaded = next(s for s in sessions if s["id"] == session["id"])
    assert len(reloaded["title"]) <= 49  # 48 + ellipsis
    assert reloaded["title"].endswith("…")


def test_prediction_linked_session_keeps_its_title_not_first_message(client, auth_headers):
    """Sessions started from a prediction already get a meaningful title --
    the first-message auto-titling should not overwrite it."""
    prediction = _upload_prediction(client, auth_headers)
    session = client.post(
        "/api/v1/chat/sessions", headers=auth_headers, json={"prediction_id": prediction["id"]}
    ).json()

    client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json={"message": "What does this mean?"},
    )

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers).json()
    reloaded = next(s for s in sessions if s["id"] == session["id"])
    assert prediction["label"] in reloaded["title"]
    assert reloaded["title"] != "What does this mean?"
    session = client.post("/api/v1/chat/sessions", headers=auth_headers, json={}).json()
    r = client.post(f"/api/v1/chat/sessions/{session['id']}/reset", headers=auth_headers)
    assert r.status_code == 204


def test_delete_session(client, auth_headers):
    session = client.post("/api/v1/chat/sessions", headers=auth_headers, json={}).json()
    client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages", headers=auth_headers, json={"message": "hi"}
    )

    r = client.delete(f"/api/v1/chat/sessions/{session['id']}", headers=auth_headers)
    assert r.status_code == 204

    # Session is gone -- further access returns 404, not a stale/empty session.
    r = client.get(f"/api/v1/chat/sessions/{session['id']}/messages", headers=auth_headers)
    assert r.status_code == 404

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers).json()
    assert session["id"] not in [s["id"] for s in sessions]


def test_delete_other_users_session_returns_404(client, auth_headers):
    session = client.post("/api/v1/chat/sessions", headers=auth_headers, json={}).json()

    other = client.post(
        "/api/v1/auth/register",
        json={"email": "other_delete_user@example.com", "password": "SecurePass123"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['tokens']['access_token']}"}

    r = client.delete(f"/api/v1/chat/sessions/{session['id']}", headers=other_headers)
    assert r.status_code == 404
