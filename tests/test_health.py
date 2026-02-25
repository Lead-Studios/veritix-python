"""Tests for GET /health and GET /ready."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from src.main import app  # noqa: E402  (must come after env setup)

client = TestClient(app)

# ---------------------------------------------------------------------------
# /health — liveness probe
# ---------------------------------------------------------------------------


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape():
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["service"] == "veritix-python"
    assert "timestamp" in data
    # timestamp must be a non-empty ISO string
    assert isinstance(data["timestamp"], str) and data["timestamp"]


# ---------------------------------------------------------------------------
# /ready — readiness probe (all checks pass)
# ---------------------------------------------------------------------------


def _mock_ok_connection():
    """Return a context-manager mock that simulates a successful SELECT 1."""
    conn = MagicMock()
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute = MagicMock()
    engine = MagicMock()
    engine.connect.return_value = conn
    return engine


def test_ready_all_ok(respx_mock=None):
    ok_engine = _mock_ok_connection()

    import httpx as _httpx

    with (
        patch("src.routers.health.get_engine", return_value=ok_engine),
        patch(
            "src.routers.health.httpx.get",
            return_value=_httpx.Response(200),
        ),
    ):
        response = client.get("/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["nest_api"] == "ok"
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# /ready — database fails
# ---------------------------------------------------------------------------


def test_ready_database_fail():
    import httpx as _httpx

    with (
        patch(
            "src.routers.health.get_engine",
            side_effect=Exception("connection refused"),
        ),
        patch(
            "src.routers.health.httpx.get",
            return_value=_httpx.Response(200),
        ),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["database"] == "error"
    assert data["checks"]["nest_api"] == "ok"


# ---------------------------------------------------------------------------
# /ready — NestJS API fails
# ---------------------------------------------------------------------------


def test_ready_nest_api_fail():
    ok_engine = _mock_ok_connection()

    with (
        patch("src.routers.health.get_engine", return_value=ok_engine),
        patch(
            "src.routers.health.httpx.get",
            side_effect=Exception("connection timeout"),
        ),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["nest_api"] == "error"


# ---------------------------------------------------------------------------
# /ready — both checks fail
# ---------------------------------------------------------------------------


def test_ready_both_fail():
    with (
        patch(
            "src.routers.health.get_engine",
            side_effect=Exception("db down"),
        ),
        patch(
            "src.routers.health.httpx.get",
            side_effect=Exception("api down"),
        ),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["database"] == "error"
    assert data["checks"]["nest_api"] == "error"


# ---------------------------------------------------------------------------
# Both endpoints must be reachable without auth headers
# ---------------------------------------------------------------------------


def test_health_no_auth_required():
    """No Authorization header — must still return 200."""
    response = client.get("/health", headers={})
    assert response.status_code == 200


def test_ready_no_auth_required():
    """No Authorization header — must return 200 or 503, never 401/403."""
    ok_engine = _mock_ok_connection()

    import httpx as _httpx

    with (
        patch("src.routers.health.get_engine", return_value=ok_engine),
        patch(
            "src.routers.health.httpx.get",
            return_value=_httpx.Response(200),
        ),
    ):
        response = client.get("/ready", headers={})

    assert response.status_code in (200, 503)
    assert response.status_code not in (401, 403)