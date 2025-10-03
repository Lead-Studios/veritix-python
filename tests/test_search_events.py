"""Tests for search-events endpoint."""
import os
os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_search_events_music_lagos_weekend():
    """Test searching for music events in Lagos this weekend."""
    payload = {"query": "music events in Lagos this weekend"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['query'] == "music events in Lagos this weekend"
    assert data['count'] > 0
    assert 'results' in data
    assert 'keywords_extracted' in data
    
    # Check that results contain music events in Lagos
    for event in data['results']:
        assert 'Lagos' in event['location']
        assert event['event_type'] == 'music'


def test_search_events_sports_lagos():
    """Test searching for sports events in Lagos."""
    payload = {"query": "sports events in Lagos"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['count'] > 0
    
    # Check that results contain sports events in Lagos
    for event in data['results']:
        assert event['event_type'] == 'sports'
        assert 'Lagos' in event['location']


def test_search_events_tech_conference():
    """Test searching for tech conferences."""
    payload = {"query": "tech conference"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['count'] > 0
    
    # Check that results contain tech or conference events
    for event in data['results']:
        assert event['event_type'] in ['tech', 'conference']


def test_search_events_location_only():
    """Test searching by location only."""
    payload = {"query": "events in Abuja"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['count'] > 0
    
    # Check that all results are in Abuja
    for event in data['results']:
        assert 'Abuja' in event['location']


def test_search_events_this_weekend():
    """Test searching for events this weekend."""
    payload = {"query": "events this weekend"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return weekend events
    assert data['count'] >= 0
    assert 'keywords_extracted' in data
    assert data['keywords_extracted']['time_filter'] == 'this_weekend'


def test_search_events_empty_results():
    """Test searching for events that don't exist."""
    payload = {"query": "ice hockey tournament in Antarctica"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # May return 0 results for non-existent events
    assert data['count'] >= 0
    assert 'results' in data


def test_search_events_general_query():
    """Test a general search query."""
    payload = {"query": "events"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return all events for a general query
    assert data['count'] > 0


def test_search_events_multiple_keywords():
    """Test searching with multiple keywords."""
    payload = {"query": "music festival Lagos this weekend"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['count'] >= 0
    assert 'keywords_extracted' in data


def test_search_events_response_structure():
    """Test that response has correct structure."""
    payload = {"query": "tech events"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert 'query' in data
    assert 'results' in data
    assert 'count' in data
    assert 'keywords_extracted' in data
    
    # Check event structure if results exist
    if data['count'] > 0:
        event = data['results'][0]
        assert 'id' in event
        assert 'name' in event
        assert 'description' in event
        assert 'event_type' in event
        assert 'location' in event
        assert 'date' in event
        assert 'price' in event
        assert 'capacity' in event


def test_search_events_invalid_empty_query():
    """Test that empty query is rejected."""
    payload = {"query": ""}
    response = client.post("/search-events", json=payload)
    
    # Should return 422 for validation error (empty string not allowed)
    assert response.status_code == 422


def test_search_events_food_festival():
    """Test searching for food events."""
    payload = {"query": "food festival Lagos"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    if data['count'] > 0:
        # Check that results contain food events
        for event in data['results']:
            assert event['event_type'] == 'food' or 'food' in event['name'].lower()


def test_search_events_comedy_show():
    """Test searching for entertainment/comedy events."""
    payload = {"query": "comedy show Lagos"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    if data['count'] > 0:
        # Check that results contain entertainment events
        for event in data['results']:
            assert event['event_type'] == 'entertainment' or 'comedy' in event['name'].lower()


def test_search_events_keyword_extraction():
    """Test that keyword extraction works correctly."""
    payload = {"query": "music events in Lagos this weekend"}
    response = client.post("/search-events", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    keywords = data['keywords_extracted']
    
    # Check that keywords were extracted correctly
    assert 'music' in keywords['event_types']
    assert 'Lagos' in keywords['locations']
    assert keywords['time_filter'] == 'this_weekend'


def test_search_events_case_insensitive():
    """Test that search is case-insensitive."""
    payload1 = {"query": "MUSIC EVENTS IN LAGOS"}
    payload2 = {"query": "music events in lagos"}
    
    response1 = client.post("/search-events", json=payload1)
    response2 = client.post("/search-events", json=payload2)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Both should return similar results (same count)
    assert response1.json()['count'] == response2.json()['count']
