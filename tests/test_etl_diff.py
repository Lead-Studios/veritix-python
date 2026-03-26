"""Tests for Issue #163: GET /etl/diff dry-run endpoint."""
import os

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.etl import diff_etl_output

client = TestClient(app)

ADMIN_KEY = "default_admin_secret_change_me"


# ---------------------------------------------------------------------------
# diff_etl_output unit tests
# ---------------------------------------------------------------------------


def test_diff_etl_output_returns_empty_when_no_engine():
    """diff_etl_output returns zeros when DB is not configured."""
    import src.etl as etl_mod

    with patch.object(etl_mod, "_pg_engine", return_value=None):
        result = diff_etl_output(
            [{"event_id": "E1", "event_name": "A", "total_tickets": 10, "total_revenue": 100.0}],
            [{"event_id": "E1", "sale_date": "2026-01-01", "tickets_sold": 5, "revenue": 50.0}],
        )

    assert result["events"]["would_insert"] == 0
    assert result["events"]["would_update"] == 0
    assert result["events"]["unchanged"] == 0
    assert result["daily"]["would_insert"] == 0


def test_diff_etl_output_detects_new_rows():
    """diff_etl_output counts new rows as would_insert when table is empty."""
    import src.etl as etl_mod
    import src.db as db_mod

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([]))

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    with patch.object(etl_mod, "_pg_engine", return_value=mock_engine):
        result = diff_etl_output(
            [{"event_id": "E1", "event_name": "A", "total_tickets": 10, "total_revenue": 100.0}],
            [{"event_id": "E1", "sale_date": "2026-01-01", "tickets_sold": 5, "revenue": 50.0}],
        )

    assert result["events"]["would_insert"] == 1
    assert result["daily"]["would_insert"] == 1


def test_diff_etl_output_detects_unchanged_rows():
    """diff_etl_output counts unchanged rows correctly."""
    import src.etl as etl_mod

    event_rows_from_db = [("E1", 10, 100.0)]
    daily_rows_from_db = [("E1", "2026-01-01", 5, 50.0)]

    call_count = [0]

    def make_mock_result(rows):
        m = MagicMock()
        m.__iter__ = MagicMock(return_value=iter(rows))
        return m

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    results_queue = [make_mock_result(event_rows_from_db), make_mock_result(daily_rows_from_db)]

    def execute_side_effect(*args, **kwargs):
        return results_queue.pop(0)

    mock_conn.execute.side_effect = execute_side_effect
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    with patch.object(etl_mod, "_pg_engine", return_value=mock_engine):
        result = diff_etl_output(
            [{"event_id": "E1", "event_name": "A", "total_tickets": 10, "total_revenue": 100.0}],
            [{"event_id": "E1", "sale_date": "2026-01-01", "tickets_sold": 5, "revenue": 50.0}],
        )

    assert result["events"]["unchanged"] == 1
    assert result["daily"]["unchanged"] == 1


def test_diff_etl_output_detects_updated_rows():
    """diff_etl_output counts modified rows as would_update."""
    import src.etl as etl_mod

    # DB has E1 with 10 tickets; transform produced 15 tickets → update
    event_rows_from_db = [("E1", 10, 100.0)]
    daily_rows_from_db = [("E1", "2026-01-01", 5, 50.0)]

    def make_mock_result(rows):
        m = MagicMock()
        m.__iter__ = MagicMock(return_value=iter(rows))
        return m

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    results_queue = [make_mock_result(event_rows_from_db), make_mock_result(daily_rows_from_db)]

    def execute_side_effect(*args, **kwargs):
        return results_queue.pop(0)

    mock_conn.execute.side_effect = execute_side_effect
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    with patch.object(etl_mod, "_pg_engine", return_value=mock_engine):
        result = diff_etl_output(
            [{"event_id": "E1", "event_name": "A", "total_tickets": 15, "total_revenue": 150.0}],
            [{"event_id": "E1", "sale_date": "2026-01-01", "tickets_sold": 8, "revenue": 80.0}],
        )

    assert result["events"]["would_update"] == 1
    assert result["daily"]["would_update"] == 1


def test_diff_etl_output_empty_inputs():
    """diff_etl_output handles empty event_rows and daily_rows gracefully."""
    import src.etl as etl_mod

    with patch.object(etl_mod, "_pg_engine", return_value=None):
        result = diff_etl_output([], [])

    assert result["events"]["would_insert"] == 0
    assert result["daily"]["would_insert"] == 0


# ---------------------------------------------------------------------------
# GET /etl/diff API tests
# ---------------------------------------------------------------------------


def test_etl_diff_requires_admin_key():
    """GET /etl/diff returns 403 when admin key is missing."""
    response = client.get("/etl/diff")
    assert response.status_code == 403


def test_etl_diff_returns_403_with_wrong_key():
    """GET /etl/diff returns 403 with incorrect admin key."""
    response = client.get("/etl/diff", headers={"X-Admin-Key": "wrong_key"})
    assert response.status_code == 403


def test_etl_diff_sync_path_returns_result():
    """GET /etl/diff returns diff result synchronously for fast extracts."""
    import src.etl as etl_mod

    mock_events = []
    mock_sales = []

    with (
        patch.object(etl_mod, "extract_events_and_sales", return_value=(mock_events, mock_sales)),
        patch.object(etl_mod, "_pg_engine", return_value=None),
    ):
        response = client.get("/etl/diff", headers={"X-Admin-Key": ADMIN_KEY})

    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "daily" in data
    assert "would_insert" in data["events"]
    assert "would_update" in data["events"]
    assert "unchanged" in data["events"]
