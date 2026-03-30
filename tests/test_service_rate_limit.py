import pytest
from fastapi.testclient import TestClient
from src.auth.dependencies import require_service_key
from src.core.ratelimit import limiter
from src.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def enable_limiter_for_test():
    limiter.enabled = True
    limiter._storage.reset()
    app.dependency_overrides[require_service_key] = lambda: "mocked_token"
    yield
    limiter._storage.reset()
    limiter.enabled = False
    app.dependency_overrides.clear()


def make_predict_payload() -> dict[str, list[int]]:
    return {"features": [1, 2, 3, 4, 5, 6]}


def make_fraud_payload() -> dict[str, list[dict[str, str]]]:
    return {
        "events": [
            {
                "type": "purchase",
                "user": "test_user",
                "ip": "1.2.3.4",
                "ticket_id": "T1",
                "timestamp": "2024-01-01T00:00:00",
            }
        ]
    }


def test_check_fraud_rate_limit():
    payload = make_fraud_payload()
    for _ in range(30):
        response = client.post("/check-fraud", json=payload)
        assert response.status_code == 200

    response_429 = client.post("/check-fraud", json=payload)
    assert response_429.status_code == 429


def test_predict_scalper_rate_limit():
    payload = make_predict_payload()
    for _ in range(60):
        response = client.post("/predict-scalper", json=payload)
        assert response.status_code in {200, 503}

    response_429 = client.post("/predict-scalper", json=payload)
    assert response_429.status_code == 429


def test_check_fraud_event_limit_exceeded():
    payload = {"events": [{"type": "purchase", "user": "test_user", "ip": "1.2.3.4", "ticket_id": "T1", "timestamp": "2024-01-01T00:00:00"}] * 1001}
    response = client.post("/check-fraud", json=payload)
    assert response.status_code == 422


def test_predict_scalper_feature_limit_exceeded():
    payload = {"features": list(range(101))}
    response = client.post("/predict-scalper", json=payload)
    assert response.status_code == 422


def test_check_fraud_requires_service_key():
    app.dependency_overrides.clear()
    response = client.post("/check-fraud", json={"events": []})
    assert response.status_code == 401


def test_predict_scalper_requires_service_key():
    app.dependency_overrides.clear()
    response = client.post("/predict-scalper", json={"features": [1, 2, 3, 4, 5, 6]})
    assert response.status_code == 401
