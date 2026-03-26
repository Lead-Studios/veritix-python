"""Tests for issue #157: expanded location detection in extract_keywords."""
import os
import pytest

os.environ.setdefault("QR_SIGNING_KEY", "a" * 32)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test-search-location.db")
os.environ.setdefault("NEST_API_BASE_URL", "https://nest.example.test")


from src.config import get_settings
from src.search_utils import extract_keywords, filter_events_by_keywords


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_EVENTS = [
    {"id": "e1", "name": "Lagos Jazz", "description": "Jazz night", "event_type": "music", "location": "Lagos", "city": "Lagos", "date": "2099-01-01"},
    {"id": "e2", "name": "Owerri Cultural Night", "description": "Culture event", "event_type": "culture", "location": "Owerri", "city": "Owerri", "date": "2099-01-01"},
    {"id": "e3", "name": "Warri Comedy", "description": "Comedy show", "event_type": "entertainment", "location": "Warri", "city": "Warri", "date": "2099-01-01"},
    {"id": "e4", "name": "Abuja Summit", "description": "Tech summit", "event_type": "conference", "location": "Abuja", "city": "Abuja", "date": "2099-01-01"},
]


# ---------------------------------------------------------------------------
# Test: known city exact match
# ---------------------------------------------------------------------------

def test_known_city_exact_match_lagos(monkeypatch):
    """Known city 'lagos' should appear in detected_locations."""
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    get_settings.cache_clear()

    result = extract_keywords("music events in Lagos")
    assert "Lagos" in result["locations"]
    assert result["fuzzy_locations"] == []


def test_known_city_exact_match_owerri(monkeypatch):
    """Owerri is in the expanded default KNOWN_LOCATIONS."""
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    get_settings.cache_clear()

    result = extract_keywords("events in Owerri this weekend")
    assert "Owerri" in result["locations"]
    assert result["fuzzy_locations"] == []


def test_known_city_filter_returns_matching_events(monkeypatch):
    """filter_events_by_keywords should return only Lagos events when Lagos is detected."""
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    get_settings.cache_clear()

    kw = extract_keywords("events in Lagos")
    filtered = filter_events_by_keywords(SAMPLE_EVENTS, kw)
    assert all(e["city"] == "Lagos" for e in filtered)
    assert len(filtered) == 1


# ---------------------------------------------------------------------------
# Test: unknown city fuzzy match
# ---------------------------------------------------------------------------

def test_unknown_city_fuzzy_match_detected(monkeypatch):
    """A city not in KNOWN_LOCATIONS should land in fuzzy_locations."""
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    monkeypatch.setenv("KNOWN_LOCATIONS", "lagos,abuja")  # exclude warri
    get_settings.cache_clear()

    result = extract_keywords("comedy events in Warri")
    assert "warri" in result["fuzzy_locations"]
    assert result["locations"] == []


def test_unknown_city_fuzzy_filter_returns_matching_events(monkeypatch):
    """filter_events_by_keywords should fuzzy-match Warri events when Warri is unknown."""
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    monkeypatch.setenv("KNOWN_LOCATIONS", "lagos,abuja")  # exclude warri
    get_settings.cache_clear()

    kw = extract_keywords("events in Warri")
    filtered = filter_events_by_keywords(SAMPLE_EVENTS, kw)
    assert any(e["city"] == "Warri" for e in filtered)
    assert all(e["city"] == "Warri" for e in filtered)


# ---------------------------------------------------------------------------
# Test: no location in query
# ---------------------------------------------------------------------------

def test_no_location_in_query_returns_all(monkeypatch):
    """When no location is specified, all events are returned."""
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    get_settings.cache_clear()

    kw = extract_keywords("music events this weekend")
    assert kw["locations"] == []
    assert kw["fuzzy_locations"] == []
    # All events pass the location filter (only event_type / time_filter may narrow results)
    music_events = [e for e in SAMPLE_EVENTS if e["event_type"] == "music"]
    filtered = filter_events_by_keywords(music_events, kw)
    assert len(filtered) == len(music_events)


# ---------------------------------------------------------------------------
# Test: KNOWN_LOCATIONS env var is respected
# ---------------------------------------------------------------------------

def test_known_locations_env_var_respected(monkeypatch):
    """Setting KNOWN_LOCATIONS env var changes detected cities."""
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://nest.example.test")
    monkeypatch.setenv("KNOWN_LOCATIONS", "ibadan,jos")
    get_settings.cache_clear()

    result = extract_keywords("events in Ibadan")
    assert "Ibadan" in result["locations"]

    result2 = extract_keywords("events in Lagos")
    assert "Lagos" not in result2["locations"]
    assert "lagos" in result2["fuzzy_locations"]
