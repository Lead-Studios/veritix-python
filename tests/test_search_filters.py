"""Tests for Issue #158: price range and capacity filters in /search-events."""
import os

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from fastapi.testclient import TestClient
from src.main import app
from src.search_utils import extract_keywords, filter_events_by_keywords

client = TestClient(app)

# Sample events for unit-level filter tests
SAMPLE_EVENTS = [
    {"id": "e1", "name": "Free Concert", "description": "Free music", "event_type": "music",
     "location": "Lagos", "date": "2026-06-01", "price": 0.0, "capacity": 200},
    {"id": "e2", "name": "Budget Seminar", "description": "Tech workshop", "event_type": "tech",
     "location": "Abuja", "date": "2026-06-02", "price": 3000.0, "capacity": 100},
    {"id": "e3", "name": "VIP Gala", "description": "Premium dinner", "event_type": "entertainment",
     "location": "Lagos", "date": "2026-06-03", "price": 25000.0, "capacity": 50},
    {"id": "e4", "name": "Sports Day", "description": "Marathon", "event_type": "sports",
     "location": "Kano", "date": "2026-06-04", "price": 5000.0, "capacity": 1000},
]


# ---------------------------------------------------------------------------
# NLP price-intent extraction
# ---------------------------------------------------------------------------

def test_extract_keywords_free_sets_max_price_zero():
    kw = extract_keywords("free music events")
    assert kw["max_price"] == 0.0


def test_extract_keywords_cheap_sets_max_price():
    kw = extract_keywords("cheap events in Lagos")
    assert kw["max_price"] == 5000.0


def test_extract_keywords_affordable_sets_max_price():
    kw = extract_keywords("affordable concert this weekend")
    assert kw["max_price"] == 5000.0


def test_extract_keywords_premium_sets_min_price():
    kw = extract_keywords("premium VIP gala")
    assert kw["min_price"] == 10000.0


def test_extract_keywords_no_price_intent():
    kw = extract_keywords("music events in Lagos")
    assert kw["min_price"] is None
    assert kw["max_price"] is None


def test_extract_keywords_has_max_capacity_none_by_default():
    kw = extract_keywords("tech conference")
    assert kw["max_capacity"] is None


# ---------------------------------------------------------------------------
# filter_events_by_keywords — price filters
# ---------------------------------------------------------------------------

def test_filter_max_price_zero_returns_free_events():
    kw = extract_keywords("free events")
    results = filter_events_by_keywords(SAMPLE_EVENTS, kw)
    assert all(e["price"] == 0.0 for e in results)
    assert any(e["id"] == "e1" for e in results)


def test_filter_max_price_explicit_overrides_nlp():
    kw = extract_keywords("music events")  # no NLP price hint
    results = filter_events_by_keywords(SAMPLE_EVENTS, kw, max_price=5000.0)
    for e in results:
        assert e["price"] <= 5000.0


def test_filter_min_price_explicit():
    kw = extract_keywords("events")
    results = filter_events_by_keywords(SAMPLE_EVENTS, kw, min_price=10000.0)
    assert all(e["price"] >= 10000.0 for e in results)
    assert any(e["id"] == "e3" for e in results)


def test_filter_min_and_max_price_combined():
    kw = extract_keywords("events")
    results = filter_events_by_keywords(SAMPLE_EVENTS, kw, min_price=2000.0, max_price=6000.0)
    for e in results:
        assert 2000.0 <= e["price"] <= 6000.0


def test_filter_max_capacity():
    kw = extract_keywords("events")
    results = filter_events_by_keywords(SAMPLE_EVENTS, kw, max_capacity=100)
    assert all(e["capacity"] <= 100 for e in results)


def test_filter_price_and_capacity_combined():
    kw = extract_keywords("events")
    results = filter_events_by_keywords(SAMPLE_EVENTS, kw, max_price=10000.0, max_capacity=200)
    for e in results:
        assert e["price"] <= 10000.0
        assert e["capacity"] <= 200


# ---------------------------------------------------------------------------
# /search-events API — price/capacity filter params
# ---------------------------------------------------------------------------

def test_search_events_max_price_filter():
    payload = {"query": "events", "max_price": 5000.0}
    response = client.post("/search-events", json=payload)
    assert response.status_code == 200
    data = response.json()
    for event in data["results"]:
        assert event["price"] <= 5000.0


def test_search_events_min_price_filter():
    payload = {"query": "events", "min_price": 8000.0}
    response = client.post("/search-events", json=payload)
    assert response.status_code == 200
    data = response.json()
    for event in data["results"]:
        assert event["price"] >= 8000.0


def test_search_events_max_capacity_filter():
    payload = {"query": "events", "max_capacity": 500}
    response = client.post("/search-events", json=payload)
    assert response.status_code == 200
    data = response.json()
    for event in data["results"]:
        assert event["capacity"] <= 500


def test_search_events_nlp_cheap_keyword():
    payload = {"query": "cheap music events in Lagos"}
    response = client.post("/search-events", json=payload)
    assert response.status_code == 200
    data = response.json()
    for event in data["results"]:
        assert event["price"] <= 5000.0


def test_search_events_price_filters_in_keywords_extracted():
    payload = {"query": "events", "max_price": 3000.0, "max_capacity": 200}
    response = client.post("/search-events", json=payload)
    assert response.status_code == 200


def test_search_events_invalid_max_price_negative():
    payload = {"query": "events", "max_price": -1.0}
    response = client.post("/search-events", json=payload)
    assert response.status_code == 422


def test_search_events_invalid_max_capacity_zero():
    payload = {"query": "events", "max_capacity": 0}
    response = client.post("/search-events", json=payload)
    assert response.status_code == 422
