"""Tests for analytics endpoints with date-range filtering and pagination."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

from src.main import app  # noqa: E402  (must come after env setup)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_scans_data():
    """Sample scan records for testing."""
    base_time = datetime.utcnow() - timedelta(hours=2)
    return [
        {
            "id": 1,
            "ticket_id": "ticket_001",
            "scanner_id": "scanner_1",
            "scan_timestamp": (base_time + timedelta(minutes=30)).isoformat(),
            "is_valid": True,
            "location": "Gate A"
        },
        {
            "id": 2,
            "ticket_id": "ticket_002",
            "scanner_id": "scanner_2",
            "scan_timestamp": (base_time + timedelta(minutes=45)).isoformat(),
            "is_valid": False,
            "location": "Gate B"
        },
        {
            "id": 3,
            "ticket_id": "ticket_003",
            "scanner_id": "scanner_1",
            "scan_timestamp": (base_time + timedelta(minutes=60)).isoformat(),
            "is_valid": True,
            "location": "Gate A"
        }
    ]

@pytest.fixture
def sample_transfers_data():
    """Sample transfer records for testing."""
    base_time = datetime.utcnow() - timedelta(hours=1)
    return [
        {
            "id": 1,
            "ticket_id": "ticket_001",
            "from_user_id": "user_1",
            "to_user_id": "user_2",
            "transfer_timestamp": (base_time + timedelta(minutes=10)).isoformat(),
            "is_successful": True,
            "transfer_reason": "sale"
        },
        {
            "id": 2,
            "ticket_id": "ticket_002",
            "from_user_id": "user_3",
            "to_user_id": "user_4",
            "transfer_timestamp": (base_time + timedelta(minutes=20)).isoformat(),
            "is_successful": False,
            "transfer_reason": "failed_payment"
        }
    ]

@pytest.fixture
def sample_invalid_attempts_data():
    """Sample invalid attempt records for testing."""
    base_time = datetime.utcnow() - timedelta(minutes=30)
    return [
        {
            "id": 1,
            "attempt_type": "scan",
            "ticket_id": "ticket_001",
            "attempt_timestamp": (base_time + timedelta(minutes=5)).isoformat(),
            "reason": "invalid_qr",
            "ip_address": "192.168.1.100"
        },
        {
            "id": 2,
            "attempt_type": "transfer",
            "ticket_id": "ticket_002",
            "attempt_timestamp": (base_time + timedelta(minutes=10)).isoformat(),
            "reason": "unauthorized_transfer",
            "ip_address": "192.168.1.101"
        }
    ]

# ---------------------------------------------------------------------------
# /stats/scans tests
# ---------------------------------------------------------------------------

def test_scans_with_date_range_filter(sample_scans_data):
    """Test GET /stats/scans with from_ts and to_ts filters."""
    from_ts = datetime.utcnow() - timedelta(hours=3)
    to_ts = datetime.utcnow() - timedelta(minutes=30)
    
    mock_result = {
        "data": [scan for scan in sample_scans_data if from_ts <= datetime.fromisoformat(scan["scan_timestamp"].replace('Z', '+00:00')) <= to_ts],
        "total": 2,
        "page": 1,
        "limit": 100,
        "from_ts": from_ts.isoformat(),
        "to_ts": to_ts.isoformat()
    }
    
    with patch("src.main.analytics_service.get_recent_scans", return_value=mock_result):
        response = client.get("/stats/scans", params={
            "event_id": "test_event",
            "from_ts": from_ts.isoformat(),
            "to_ts": to_ts.isoformat(),
            "page": 1,
            "limit": 100
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "test_event"
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["limit"] == 100
    assert data["from_ts"] == from_ts.isoformat()
    assert data["to_ts"] == to_ts.isoformat()
    assert len(data["data"]) == 2

def test_scans_pagination_boundary(sample_scans_data):
    """Test GET /stats/scans pagination boundaries."""
    mock_result = {
        "data": [sample_scans_data[0]],  # Only first record
        "total": 3,
        "page": 1,
        "limit": 1,
        "from_ts": None,
        "to_ts": None
    }
    
    with patch("src.main.analytics_service.get_recent_scans", return_value=mock_result):
        response = client.get("/stats/scans", params={
            "event_id": "test_event",
            "page": 1,
            "limit": 1
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["limit"] == 1
    assert len(data["data"]) == 1

def test_scans_empty_result():
    """Test GET /stats/scans with no matching records."""
    future_time = datetime.utcnow() + timedelta(hours=24)
    
    mock_result = {
        "data": [],
        "total": 0,
        "page": 1,
        "limit": 100,
        "from_ts": future_time.isoformat(),
        "to_ts": (future_time + timedelta(hours=1)).isoformat()
    }
    
    with patch("src.main.analytics_service.get_recent_scans", return_value=mock_result):
        response = client.get("/stats/scans", params={
            "event_id": "test_event",
            "from_ts": future_time.isoformat(),
            "to_ts": (future_time + timedelta(hours=1)).isoformat()
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["data"]) == 0

def test_scans_default_parameters():
    """Test GET /stats/scans with default parameters."""
    mock_result = {
        "data": [],
        "total": 0,
        "page": 1,
        "limit": 100,
        "from_ts": None,
        "to_ts": None
    }
    
    with patch("src.main.analytics_service.get_recent_scans", return_value=mock_result):
        response = client.get("/stats/scans", params={
            "event_id": "test_event"
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 100
    assert data["from_ts"] is None
    assert data["to_ts"] is None

def test_scans_limit_validation():
    """Test GET /stats/scans limit validation (max 1000)."""
    response = client.get("/stats/scans", params={
        "event_id": "test_event",
        "limit": 1001  # Exceeds max limit
    })
    
    assert response.status_code == 422  # Validation error

def test_scans_page_validation():
    """Test GET /stats/scans page validation (minimum 1)."""
    response = client.get("/stats/scans", params={
        "event_id": "test_event",
        "page": 0  # Below minimum
    })
    
    assert response.status_code == 422  # Validation error

# ---------------------------------------------------------------------------
# /stats/transfers tests
# ---------------------------------------------------------------------------

def test_transfers_with_date_range_filter(sample_transfers_data):
    """Test GET /stats/transfers with from_ts and to_ts filters."""
    from_ts = datetime.utcnow() - timedelta(hours=2)
    to_ts = datetime.utcnow() - timedelta(minutes=15)
    
    mock_result = {
        "data": [transfer for transfer in sample_transfers_data if from_ts <= datetime.fromisoformat(transfer["transfer_timestamp"].replace('Z', '+00:00')) <= to_ts],
        "total": 1,
        "page": 1,
        "limit": 100,
        "from_ts": from_ts.isoformat(),
        "to_ts": to_ts.isoformat()
    }
    
    with patch("src.main.analytics_service.get_recent_transfers", return_value=mock_result):
        response = client.get("/stats/transfers", params={
            "event_id": "test_event",
            "from_ts": from_ts.isoformat(),
            "to_ts": to_ts.isoformat()
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "test_event"
    assert data["total"] == 1
    assert len(data["data"]) == 1

def test_transfers_pagination(sample_transfers_data):
    """Test GET /stats/transfers pagination."""
    mock_result = {
        "data": [sample_transfers_data[0]],
        "total": 2,
        "page": 2,
        "limit": 1,
        "from_ts": None,
        "to_ts": None
    }
    
    with patch("src.main.analytics_service.get_recent_transfers", return_value=mock_result):
        response = client.get("/stats/transfers", params={
            "event_id": "test_event",
            "page": 2,
            "limit": 1
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["total"] == 2
    assert len(data["data"]) == 1

# ---------------------------------------------------------------------------
# /stats/invalid-attempts tests
# ---------------------------------------------------------------------------

def test_invalid_attempts_with_date_range_filter(sample_invalid_attempts_data):
    """Test GET /stats/invalid-attempts with from_ts and to_ts filters."""
    from_ts = datetime.utcnow() - timedelta(minutes=20)
    to_ts = datetime.utcnow()
    
    mock_result = {
        "data": [attempt for attempt in sample_invalid_attempts_data if from_ts <= datetime.fromisoformat(attempt["attempt_timestamp"].replace('Z', '+00:00')) <= to_ts],
        "total": 1,
        "page": 1,
        "limit": 100,
        "from_ts": from_ts.isoformat(),
        "to_ts": to_ts.isoformat()
    }
    
    with patch("src.main.analytics_service.get_invalid_attempts", return_value=mock_result):
        response = client.get("/stats/invalid-attempts", params={
            "event_id": "test_event",
            "from_ts": from_ts.isoformat(),
            "to_ts": to_ts.isoformat()
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "test_event"
    assert data["total"] == 1
    assert len(data["data"]) == 1

def test_invalid_attempts_empty_result():
    """Test GET /stats/invalid-attempts with no matching records."""
    future_time = datetime.utcnow() + timedelta(hours=24)
    
    mock_result = {
        "data": [],
        "total": 0,
        "page": 1,
        "limit": 100,
        "from_ts": future_time.isoformat(),
        "to_ts": (future_time + timedelta(hours=1)).isoformat()
    }
    
    with patch("src.main.analytics_service.get_invalid_attempts", return_value=mock_result):
        response = client.get("/stats/invalid-attempts", params={
            "event_id": "test_event",
            "from_ts": future_time.isoformat(),
            "to_ts": (future_time + timedelta(hours=1)).isoformat()
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["data"]) == 0

# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

def test_scans_service_error():
    """Test GET /stats/scans when service raises an exception."""
    with patch("src.main.analytics_service.get_recent_scans", side_effect=Exception("Database error")):
        response = client.get("/stats/scans", params={
            "event_id": "test_event"
        })
    
    assert response.status_code == 500
    assert "Failed to retrieve recent scans" in response.json()["detail"]

def test_transfers_service_error():
    """Test GET /stats/transfers when service raises an exception."""
    with patch("src.main.analytics_service.get_recent_transfers", side_effect=Exception("Database error")):
        response = client.get("/stats/transfers", params={
            "event_id": "test_event"
        })
    
    assert response.status_code == 500
    assert "Failed to retrieve recent transfers" in response.json()["detail"]

def test_invalid_attempts_service_error():
    """Test GET /stats/invalid-attempts when service raises an exception."""
    with patch("src.main.analytics_service.get_invalid_attempts", side_effect=Exception("Database error")):
        response = client.get("/stats/invalid-attempts", params={
            "event_id": "test_event"
        })
    
    assert response.status_code == 500
    assert "Failed to retrieve invalid attempts" in response.json()["detail"]

# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

def test_all_endpoints_consistent_response_structure():
    """Test that all endpoints return consistent pagination structure."""
    mock_result = {
        "data": [],
        "total": 0,
        "page": 1,
        "limit": 100,
        "from_ts": None,
        "to_ts": None
    }
    
    with (
        patch("src.main.analytics_service.get_recent_scans", return_value=mock_result),
        patch("src.main.analytics_service.get_recent_transfers", return_value=mock_result),
        patch("src.main.analytics_service.get_invalid_attempts", return_value=mock_result)
    ):
        scans_response = client.get("/stats/scans", params={"event_id": "test_event"})
        transfers_response = client.get("/stats/transfers", params={"event_id": "test_event"})
        attempts_response = client.get("/stats/invalid-attempts", params={"event_id": "test_event"})
    
    for response in [scans_response, transfers_response, attempts_response]:
        assert response.status_code == 200
        data = response.json()
        # All should have the same pagination structure
        assert "event_id" in data
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "from_ts" in data
        assert "to_ts" in data

def test_datetime_format_handling():
    """Test that datetime parameters are properly handled."""
    from_ts = "2024-03-27T10:00:00"
    to_ts = "2024-03-27T12:00:00"
    
    mock_result = {
        "data": [],
        "total": 0,
        "page": 1,
        "limit": 100,
        "from_ts": from_ts,
        "to_ts": to_ts
    }
    
    with patch("src.main.analytics_service.get_recent_scans", return_value=mock_result):
        response = client.get("/stats/scans", params={
            "event_id": "test_event",
            "from_ts": from_ts,
            "to_ts": to_ts
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["from_ts"] == from_ts
    assert data["to_ts"] == to_ts
