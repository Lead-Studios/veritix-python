import pytest
import json
from src.app import app, analyze_sentiment

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    with app.test_client() as client:
        yield client


# ---------- Unit tests for analyze_sentiment ----------
def test_analyze_sentiment_positive():
    result = analyze_sentiment("This event was fantastic and enjoyable!")
    assert result['sentiment'] == 'positive'
    assert result['polarity'] > 0

def test_analyze_sentiment_negative():
    result = analyze_sentiment("This was the worst event ever, terrible experience.")
    assert result['sentiment'] == 'negative'
    assert result['polarity'] < 0

def test_analyze_sentiment_neutral():
    result = analyze_sentiment("The event happened.")
    assert result['sentiment'] == 'neutral'
    assert result['polarity'] == 0.0 or abs(result['polarity']) <= 0.1

def test_analyze_sentiment_empty_text():
    result = analyze_sentiment("   ")
    assert result['sentiment'] == 'neutral'
    assert result['polarity'] == 0.0
    assert result['message'] == 'Empty text provided'


# ---------- Integration tests for Flask endpoints ----------
def test_health_check(client):
    response = client.get('/health')
    data = response.get_json()
    assert response.status_code == 200
    assert data['status'] == 'healthy'


def test_analyze_review_valid(client):
    payload = {"text": "I really loved this event, it was well organized!"}
    response = client.post('/analyze-review', json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert data['success'] is True
    assert data['analysis']['sentiment'] == 'positive'


def test_analyze_review_no_json(client):
    response = client.post('/analyze-review', data="not json")
    data = response.get_json()
    assert response.status_code == 400
    assert 'error' in data


def test_analyze_review_missing_text_field(client):
    response = client.post('/analyze-review', json={})
    data = response.get_json()
    assert response.status_code == 400
    assert 'error' in data
