import os

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from src.main import app


if not any(getattr(route, "path", None) == "/__test/unhandled-exception" for route in app.router.routes):
    @app.get("/__test/unhandled-exception")
    def _raise_unhandled_exception():
        raise RuntimeError("boom")


def test_global_exception_handler_returns_safe_json_in_production(monkeypatch):
    monkeypatch.setenv("DEBUG", "false")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/__test/unhandled-exception")

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error": "Internal server error",
        "detail": None,
    }


def test_global_exception_handler_includes_detail_in_debug(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/__test/unhandled-exception")
    body = response.json()

    assert response.status_code == 500
    assert body["success"] is False
    assert body["error"] == "Internal server error"
    assert body["detail"] == "boom"


def test_http_exception_handler_returns_consistent_shape():
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/recommend-events", json={"user_id": "missing-user"})
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["status_code"] == 404
    assert body["error"] == "User not found"


def test_validation_exception_handler_returns_field_level_errors():
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/predict-scalper", json={"features": "invalid"})
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"] == "Validation error"
    assert body["status_code"] == 422
    assert isinstance(body["detail"], list)
    assert len(body["detail"]) > 0
    assert body["detail"][0]["field"] == "features"
    assert "valid list" in body["detail"][0]["message"].lower()
