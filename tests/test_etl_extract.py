import httpx
import pytest

from src.config import get_settings
from src.etl.extract import EventRecord, TicketSaleRecord, extract_events_and_sales


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
        self.calls.append({"url": url, "headers": headers or {}, "params": params})
        effect = self._side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect


def _set_required_env(monkeypatch):
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./extract-test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    get_settings.cache_clear()


def test_extract_success_with_pagination_and_auth_header(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("NEST_API_TOKEN", "secret-token")
    get_settings.cache_clear()

    calls = []
    side_effects = [
        _response(
            200,
            "https://nest.example.test/events?page=1",
            {
                "data": [{"id": "E1", "name": "Concert A"}],
                "pagination": {"page": 1, "total_pages": 2},
            },
        ),
        _response(
            200,
            "https://nest.example.test/events?page=2",
            {
                "data": [{"id": "E2", "name": "Concert B"}],
                "pagination": {"page": 2, "total_pages": 2},
            },
        ),
        _response(
            200,
            "https://nest.example.test/ticket-sales",
            {
                "data": [{"event_id": "E1", "quantity": 2, "price": 10.0, "sale_date": "2025-10-01T00:00:00"}]
            },
        ),
    ]
    monkeypatch.setattr(
        "src.etl.extract.httpx.Client",
        lambda timeout: DummyClient(side_effects=side_effects, calls=calls),
    )

    events, sales = extract_events_and_sales()

    assert len(events) == 2
    assert len(sales) == 1
    assert all(isinstance(event, EventRecord) for event in events)
    assert all(isinstance(sale, TicketSaleRecord) for sale in sales)
    assert calls[0]["headers"]["Authorization"] == "Bearer secret-token"
    assert calls[0]["params"] == {"page": 1}
    assert calls[1]["params"] == {"page": 2}


def test_extract_retries_on_503(monkeypatch):
    _set_required_env(monkeypatch)
    calls = []
    sleep_calls = []

    side_effects = [
        _response(503, "https://nest.example.test/events?page=1", {"data": []}),
        _response(
            200,
            "https://nest.example.test/events?page=1",
            {"data": [{"id": "E1", "name": "Concert A"}], "pagination": {"page": 1, "total_pages": 1}},
        ),
        _response(200, "https://nest.example.test/ticket-sales", {"data": []}),
    ]
    monkeypatch.setattr(
        "src.etl.extract.httpx.Client",
        lambda timeout: DummyClient(side_effects=side_effects, calls=calls),
    )
    monkeypatch.setattr("src.etl.extract.time.sleep", lambda seconds: sleep_calls.append(seconds))

    events, sales = extract_events_and_sales()

    assert len(events) == 1
    assert sales == []
    assert len(calls) == 3
    assert sleep_calls == [1]


def test_extract_aborts_on_401_without_retry(monkeypatch):
    _set_required_env(monkeypatch)
    calls = []
    sleep_calls = []

    side_effects = [
        _response(401, "https://nest.example.test/events?page=1", {"message": "Unauthorized"}),
    ]
    monkeypatch.setattr(
        "src.etl.extract.httpx.Client",
        lambda timeout: DummyClient(side_effects=side_effects, calls=calls),
    )
    monkeypatch.setattr("src.etl.extract.time.sleep", lambda seconds: sleep_calls.append(seconds))

    with pytest.raises(httpx.HTTPStatusError):
        extract_events_and_sales()

    assert len(calls) == 1
    assert sleep_calls == []
