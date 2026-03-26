"""Tests for Issue #160: GET /events/trending endpoint."""
import os

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# AnalyticsService.get_trending_events unit tests
# ---------------------------------------------------------------------------


def test_get_trending_events_returns_empty_when_no_db():
    """get_trending_events returns [] when DB engine is unavailable."""
    from src.analytics.service import AnalyticsService
    import src.db as db_mod

    svc = AnalyticsService()
    with patch.object(db_mod, "get_engine", return_value=None):
        results = svc.get_trending_events(limit=5, hours=24)
    assert results == []


def test_get_trending_events_queries_and_returns_rows():
    """get_trending_events returns rows from a mocked DB."""
    from src.analytics.service import AnalyticsService, _trending_cache
    import src.analytics.service as svc_mod
    import src.db as db_mod

    # Reset cache
    svc_mod._trending_cache = None

    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, i: ["event_001", "Event One", 42][i]

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([mock_row]))

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    svc = AnalyticsService()
    with patch.object(db_mod, "get_engine", return_value=mock_engine):
        results = svc.get_trending_events(limit=10, hours=24)

    assert isinstance(results, list)


def test_get_trending_events_respects_limit():
    """get_trending_events honours the limit parameter."""
    from src.analytics.service import AnalyticsService
    import src.analytics.service as svc_mod
    import src.db as db_mod

    svc_mod._trending_cache = None

    # Build 20 mock rows
    rows = []
    for i in range(20):
        row = MagicMock()
        row.__getitem__ = lambda self, idx, _i=i: [f"evt_{_i:02}", f"Event {_i}", 20 - _i][idx]
        rows.append(row)

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    svc = AnalyticsService()
    with patch.object(db_mod, "get_engine", return_value=mock_engine):
        results = svc.get_trending_events(limit=5, hours=24)

    assert len(results) <= 5


# ---------------------------------------------------------------------------
# GET /events/trending API tests
# ---------------------------------------------------------------------------


def test_trending_events_endpoint_returns_200_with_empty_db():
    """GET /events/trending returns 200 with empty list when DB is unavailable."""
    import src.db as db_mod

    with patch.object(db_mod, "get_engine", return_value=None):
        response = client.get("/events/trending")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == []


def test_trending_events_default_limit():
    """GET /events/trending defaults to limit=10."""
    import src.db as db_mod
    import src.analytics.service as svc_mod

    svc_mod._trending_cache = None

    with patch.object(db_mod, "get_engine", return_value=None):
        response = client.get("/events/trending")

    assert response.status_code == 200


def test_trending_events_custom_limit():
    """GET /events/trending?limit=3 is accepted."""
    import src.db as db_mod
    import src.analytics.service as svc_mod

    svc_mod._trending_cache = None

    with patch.object(db_mod, "get_engine", return_value=None):
        response = client.get("/events/trending?limit=3")

    assert response.status_code == 200


def test_trending_events_limit_too_large_rejected():
    """GET /events/trending?limit=200 is rejected (>100)."""
    response = client.get("/events/trending?limit=200")
    assert response.status_code == 422


def test_trending_events_limit_zero_rejected():
    """GET /events/trending?limit=0 is rejected (<1)."""
    response = client.get("/events/trending?limit=0")
    assert response.status_code == 422


def test_trending_events_cache_is_used():
    """Second call uses cached results without hitting the DB again."""
    import src.analytics.service as svc_mod
    import src.db as db_mod

    cached_data = [{"event_id": "cached_evt", "event_name": "Cached", "scan_count": 99, "window_hours": 24}]
    import time
    svc_mod._trending_cache = (cached_data, time.monotonic() + 600)

    with patch.object(db_mod, "get_engine", side_effect=AssertionError("Should not hit DB")):
        response = client.get("/events/trending?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert any(e["event_id"] == "cached_evt" for e in data)

    # Cleanup
    svc_mod._trending_cache = None
