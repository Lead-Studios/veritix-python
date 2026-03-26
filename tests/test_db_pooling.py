"""Tests for Issue #164: database connection pooling (src/db.py) and /health/db endpoint."""
import os
import sys

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

import pytest
from unittest.mock import MagicMock, patch

from src.config import get_settings


# ---------------------------------------------------------------------------
# Config: POOL_SIZE / POOL_MAX_OVERFLOW
# ---------------------------------------------------------------------------


def test_settings_pool_defaults():
    """POOL_SIZE and POOL_MAX_OVERFLOW are present with correct defaults."""
    settings = get_settings()
    assert settings.POOL_SIZE == 5
    assert settings.POOL_MAX_OVERFLOW == 10


# ---------------------------------------------------------------------------
# src.db module
# ---------------------------------------------------------------------------


def test_db_get_engine_returns_none_when_no_url():
    """get_engine() returns None gracefully when DATABASE_URL is not configured."""
    import src.db as db_mod

    original_engine = db_mod._engine
    try:
        db_mod._engine = None
        with patch("src.db.get_settings") as mock_settings:
            mock_settings.return_value.DATABASE_URL = ""
            engine = db_mod.get_engine()
        assert engine is None
    finally:
        db_mod._engine = original_engine


def test_db_get_session_returns_none_when_no_engine():
    """get_session() returns None when engine is unavailable."""
    import src.db as db_mod

    with patch.object(db_mod, "get_engine", return_value=None):
        session = db_mod.get_session()
    assert session is None


def test_db_get_pool_status_unavailable_when_no_engine():
    """get_pool_status() returns unavailable status when engine is None."""
    import src.db as db_mod

    with patch.object(db_mod, "get_engine", return_value=None):
        status = db_mod.get_pool_status()
    assert status["status"] == "unavailable"


def test_db_get_pool_status_returns_dict_with_engine():
    """get_pool_status() returns pool stats dict when engine exists."""
    import src.db as db_mod

    mock_pool = MagicMock()
    mock_pool.size.return_value = 5
    mock_pool.checkedin.return_value = 4
    mock_pool.checkedout.return_value = 1
    mock_pool.overflow.return_value = 0
    mock_pool.invalid.return_value = 0

    mock_engine = MagicMock()
    mock_engine.pool = mock_pool

    with patch.object(db_mod, "get_engine", return_value=mock_engine):
        status = db_mod.get_pool_status()

    assert status["pool_size"] == 5
    assert status["checked_in"] == 4
    assert status["checked_out"] == 1
    assert "overflow" in status
    assert "invalid" in status


# ---------------------------------------------------------------------------
# /health/db endpoint
# ---------------------------------------------------------------------------


def test_health_db_returns_503_when_no_database():
    """GET /health/db returns 503 when the database engine is unavailable."""
    from fastapi.testclient import TestClient
    from src.main import app
    import src.db as db_mod

    with patch.object(db_mod, "get_engine", return_value=None):
        client = TestClient(app)
        response = client.get("/health/db")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "error"


def test_health_db_returns_200_when_database_ok():
    """GET /health/db returns 200 with pool stats when DB is reachable."""
    from fastapi.testclient import TestClient
    from src.main import app
    import src.db as db_mod
    from sqlalchemy.engine import Connection

    mock_conn = MagicMock(spec=Connection)
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.size.return_value = 5
    mock_pool.checkedin.return_value = 5
    mock_pool.checkedout.return_value = 0
    mock_pool.overflow.return_value = 0
    mock_pool.invalid.return_value = 0

    mock_engine = MagicMock()
    mock_engine.pool = mock_pool
    mock_engine.connect.return_value = mock_conn

    with patch.object(db_mod, "get_engine", return_value=mock_engine):
        client = TestClient(app)
        response = client.get("/health/db")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "pool" in data
    assert "timestamp" in data
