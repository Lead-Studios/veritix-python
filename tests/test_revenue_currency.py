import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.main import app
from src import currency_service

client = TestClient(app)

# Mock rates: 1 USD = 1600 NGN
MOCK_RATES = {
    "USD": 1.0,
    "NGN": 1600.0,
    "GBP": 0.78,
    "EUR": 0.92,
    "KES": 130.0
}

@pytest.fixture(autouse=True)
def mock_fx_api():
    with patch("src.currency_service.get_exchange_rates", return_value=MOCK_RATES):
        yield

def test_usd_calculation_no_conversion():
    """Test that USD calculation uses the original fixed fee ($0.30)."""
    input_data = {
        "event_id": "usd_event",
        "total_sales": 1000.0,
        "ticket_count": 10,
        "currency": "USD"
    }
    
    response = client.post("/calculate-revenue-share", json=input_data)
    assert response.status_code == 200
    data = response.json()
    
    # Fees: 2.9% of 1000 = 29.0 + (10 * 0.30) = 3.0. Total processing = 32.0
    # Platform fee: 5% of 1000 = 50.0
    # Total fees = 32.0 + 50.0 = 82.0
    assert data["total_fees"] == 82.0
    assert data["currency"] == "USD"

def test_ngn_calculation_conversion_applied():
    """Test that NGN calculation converts the fixed fee ($0.30 * 1600 = 480 NGN)."""
    input_data = {
        "event_id": "ngn_event",
        "total_sales": 100000.0,
        "ticket_count": 10,
        "currency": "NGN"
    }
    
    response = client.post("/calculate-revenue-share", json=input_data)
    assert response.status_code == 200
    data = response.json()
    
    # Processing: 2.9% of 100000 = 2900 + (10 * 0.30 * 1600) = 2900 + 4800 = 7700
    # Platform: 5% of 100000 = 5000
    # Total = 7700 + 5000 = 12700
    assert data["total_fees"] == 12700.0
    assert data["currency"] == "NGN"
    assert data["distributions"][0]["currency"] == "NGN"

def test_unsupported_currency_422():
    """Test that unsupported currency returns 422."""
    input_data = {
        "event_id": "weird_event",
        "total_sales": 100.0,
        "ticket_count": 1,
        "currency": "ZAR"  # Not in supported list
    }
    
    response = client.post("/calculate-revenue-share", json=input_data)
    assert response.status_code == 422
    # detail should mention supported list
    assert "ZAR" not in MOCK_RATES # sanity check
    assert "not supported" in response.text.lower()

def test_exchange_rates_api():
    """Test the public exchange rates API."""
    response = client.get("/revenue-share/exchange-rates")
    assert response.status_code == 200
    data = response.json()
    assert data["NGN"] == 1600.0
    assert data["USD"] == 1.0
