import os

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from src.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_chat_send_message_missing_required_field_returns_422():
    response = client.post(
        "/chat/test-conv/messages",
        json={"sender_id": "u1", "sender_type": "user"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Validation error"
    assert body["status_code"] == 422


def test_recommend_events_rejects_extra_fields():
    response = client.post(
        "/recommend-events",
        json={"user_id": "user1", "unexpected": "x"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Validation error"


def test_stats_scans_invalid_limit_returns_422():
    response = client.get("/stats/scans", params={"event_id": "evt_1", "limit": 0})

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Validation error"


def test_stats_scans_missing_event_id_returns_422():
    response = client.get("/stats/scans")

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Validation error"
