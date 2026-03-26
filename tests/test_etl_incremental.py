"""Tests for issue #161: incremental ETL extract using a cursor."""
import httpx
import pytest

from src.config import get_settings
from src.etl.extract import extract_events_and_sales


def _response(status_code: int, url: str, payload):
    request = httpx.Request("GET", url)
    return httpx.Response(status_code=status_code, json=payload, request=request)


class DummyClient:
    def __init__(self, side_effects, calls):
        self._side_effects = list(side_effects)
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers or {}, "params": params or {}})
        effect = self._side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect


def _set_env(monkeypatch):
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./incr-test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# First run — no cursor
# ---------------------------------------------------------------------------

def test_first_run_no_since_param(monkeypatch):
    """When since=None (first run), no ?since param is forwarded to the API."""
    _set_env(monkeypatch)
    calls = []
    side_effects = [
        _response(200, "https://nest.example.test/events?page=1", {"data": [{"id": "E1", "name": "Ev"}], "pagination": {"page": 1, "total_pages": 1}}),
        _response(200, "https://nest.example.test/ticket-sales", {"data": []}),
    ]
    monkeypatch.setattr("src.etl.extract.httpx.Client", lambda timeout: DummyClient(side_effects, calls))

    extract_events_and_sales(since=None)

    assert "since" not in calls[0]["params"]
    assert "since" not in calls[1]["params"]


# ---------------------------------------------------------------------------
# Subsequent run — cursor used
# ---------------------------------------------------------------------------

def test_subsequent_run_since_param_forwarded(monkeypatch):
    """When since is provided, ?since is forwarded to both /events and /ticket-sales."""
    _set_env(monkeypatch)
    since_value = "2025-10-01T00:00:00"
    calls = []
    side_effects = [
        _response(200, "https://nest.example.test/events", {"data": [{"id": "E2", "name": "Ev2"}], "pagination": {"page": 1, "total_pages": 1}}),
        _response(200, "https://nest.example.test/ticket-sales", {"data": []}),
    ]
    monkeypatch.setattr("src.etl.extract.httpx.Client", lambda timeout: DummyClient(side_effects, calls))

    extract_events_and_sales(since=since_value)

    assert calls[0]["params"].get("since") == since_value
    assert calls[1]["params"].get("since") == since_value


def test_subsequent_run_returns_records_normally(monkeypatch):
    """Incremental extract still parses and returns records correctly."""
    _set_env(monkeypatch)
    calls = []
    side_effects = [
        _response(200, "https://nest.example.test/events", {
            "data": [{"id": "E3", "name": "NewEvent"}],
            "pagination": {"page": 1, "total_pages": 1},
        }),
        _response(200, "https://nest.example.test/ticket-sales", {
            "data": [{"event_id": "E3", "quantity": 5, "price": 20.0, "sale_date": "2025-11-01T00:00:00"}],
        }),
    ]
    monkeypatch.setattr("src.etl.extract.httpx.Client", lambda timeout: DummyClient(side_effects, calls))

    events, sales = extract_events_and_sales(since="2025-10-01T00:00:00")

    assert len(events) == 1
    assert events[0].event_id == "E3"
    assert len(sales) == 1
    assert sales[0].event_id == "E3"


# ---------------------------------------------------------------------------
# Failed run — cursor not advanced
# ---------------------------------------------------------------------------

def test_failed_run_cursor_not_advanced(monkeypatch):
    """If extract raises, no cursor update happens (run_etl_once responsibility)."""
    _set_env(monkeypatch)
    calls = []
    side_effects = [
        _response(500, "https://nest.example.test/events", {}),
        _response(500, "https://nest.example.test/events", {}),
        _response(500, "https://nest.example.test/events", {}),
    ]
    monkeypatch.setattr("src.etl.extract.httpx.Client", lambda timeout: DummyClient(side_effects, calls))
    monkeypatch.setattr("src.etl.extract.time.sleep", lambda s: None)

    with pytest.raises(Exception):
        extract_events_and_sales(since="2025-10-01T00:00:00")
