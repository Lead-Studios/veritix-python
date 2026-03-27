"""Tests for GET /metrics endpoint authentication."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from src.main import app  # noqa: E402  (must come after env setup)

client = TestClient(app)

# ---------------------------------------------------------------------------
# /metrics — authentication tests
# ---------------------------------------------------------------------------


def test_metrics_without_auth_returns_401():
    """GET /metrics without Authorization header should return 401."""
    response = client.get("/metrics")
    assert response.status_code == 401
    assert "Missing or invalid authentication token" in response.text


def test_metrics_with_invalid_token_returns_403():
    """GET /metrics with invalid Bearer token should return 403."""
    response = client.get("/metrics", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 403
    assert "Invalid admin token" in response.text


def test_metrics_with_valid_token_returns_200():
    """GET /metrics with valid Bearer token should return 200."""
    # Set a non-default admin key for testing
    test_admin_key = "test_admin_key_12345"
    
    with patch("src.main.get_settings") as mock_settings:
        mock_settings.return_value.ADMIN_API_KEY = test_admin_key
        response = client.get("/metrics", headers={"Authorization": f"Bearer {test_admin_key}"})
    
    assert response.status_code == 200
    # Should return Prometheus metrics content type
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    # Should contain some Prometheus metrics
    assert "HELP" in response.text or "TYPE" in response.text


def test_metrics_with_default_key_returns_503():
    """GET /metrics when ADMIN_API_KEY is still default should return 503."""
    default_key = "default_admin_secret_change_me"
    
    with patch("src.main.get_settings") as mock_settings:
        mock_settings.return_value.ADMIN_API_KEY = default_key
        response = client.get("/metrics", headers={"Authorization": f"Bearer {default_key}"})
    
    assert response.status_code == 503
    assert "ADMIN_API_KEY not configured" in response.text
    assert "Please set a secure ADMIN_API_KEY environment variable" in response.text


def test_metrics_auth_header_case_insensitive():
    """Authorization header should work with different case variations."""
    test_admin_key = "test_admin_key_12345"
    
    with patch("src.main.get_settings") as mock_settings:
        mock_settings.return_value.ADMIN_API_KEY = test_admin_key
        
        # Test lowercase 'authorization'
        response = client.get("/metrics", headers={"authorization": f"Bearer {test_admin_key}"})
        assert response.status_code == 200
        
        # Test mixed case 'Authorization'
        response = client.get("/metrics", headers={"Authorization": f"Bearer {test_admin_key}"})
        assert response.status_code == 200


def test_metrics_with_non_bearer_scheme_returns_401():
    """GET /metrics with non-Bearer scheme should return 401."""
    response = client.get("/metrics", headers={"Authorization": "Basic dGVzdDp0ZXN0"})
    assert response.status_code == 401


def test_metrics_with_malformed_auth_header_returns_401():
    """GET /metrics with malformed Authorization header should return 401."""
    # Missing token
    response = client.get("/metrics", headers={"Authorization": "Bearer"})
    assert response.status_code == 401
    
    # Empty Authorization header
    response = client.get("/metrics", headers={"Authorization": ""})
    assert response.status_code == 401
