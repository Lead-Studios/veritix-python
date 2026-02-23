import os
import json
import csv
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.report_service import (
    generate_daily_report_csv,
    _query_daily_sales,
    _query_event_names,
    REPORTS_DIR
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_reports():
    yield
    # Cleanup after tests
    if REPORTS_DIR.exists():
        for file in REPORTS_DIR.glob("daily_report_*"):
            file.unlink()


@pytest.fixture
def mock_db_data():
    """Mock database query results"""
    sales_data = [
        {
            "event_id": "E1",
            "sale_date": "2025-10-04",
            "tickets_sold": 50,
            "revenue": 500.0
        },
        {
            "event_id": "E2",
            "sale_date": "2025-10-04",
            "tickets_sold": 30,
            "revenue": 300.0
        }
    ]
    event_names = {
        "E1": "Concert Night",
        "E2": "Tech Conference"
    }
    return sales_data, event_names


def test_generate_daily_report_csv_format(mock_db_data):
    """Test CSV report generation"""
    sales_data, event_names = mock_db_data
    
    with patch("src.report_service._query_daily_sales", return_value=sales_data), \
         patch("src.report_service._query_event_names", return_value=event_names), \
         patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 5}), \
         patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 2}):
        
        target_date = date(2025, 10, 4)
        report_path = generate_daily_report_csv(target_date=target_date, output_format="csv")
        
        assert report_path is not None
        assert Path(report_path).exists()
        assert "daily_report_2025-10-04" in report_path
        assert report_path.endswith(".csv")
        
        # Verify CSV content
        with open(report_path, "r") as f:
            content = f.read()
            assert "Daily Sales Report" in content
            assert "2025-10-04" in content
            assert "80" in content  # total sales
            assert "Concert Night" in content
            assert "Tech Conference" in content


def test_generate_daily_report_json_format(mock_db_data):
    """Test JSON report generation"""
    sales_data, event_names = mock_db_data
    
    with patch("src.report_service._query_daily_sales", return_value=sales_data), \
         patch("src.report_service._query_event_names", return_value=event_names), \
         patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 5}), \
         patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 2}):
        
        target_date = date(2025, 10, 4)
        report_path = generate_daily_report_csv(target_date=target_date, output_format="json")
        
        assert report_path is not None
        assert Path(report_path).exists()
        assert "daily_report_2025-10-04" in report_path
        assert report_path.endswith(".json")
        
        # Verify JSON content
        with open(report_path, "r") as f:
            data = json.load(f)
            assert data["report_date"] == "2025-10-04"
            assert data["summary"]["total_sales"] == 80
            assert data["summary"]["total_revenue"] == 800.0
            assert data["summary"]["total_transfers"] == 5
            assert data["summary"]["invalid_scans"] == 2
            assert len(data["sales_by_event"]) == 2


def test_endpoint_generate_daily_report_default():
    """Test /generate-daily-report endpoint with default parameters"""
    mock_sales = [
        {"event_id": "E1", "sale_date": "2025-10-04", "tickets_sold": 10, "revenue": 100.0}
    ]
    mock_names = {"E1": "Test Event"}
    
    with patch("src.report_service._query_daily_sales", return_value=mock_sales), \
         patch("src.report_service._query_event_names", return_value=mock_names), \
         patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 0}), \
         patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 0}):
        
        response = client.post("/generate-daily-report", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report_path" in data
        assert data["summary"]["total_sales"] == 10
        assert data["summary"]["total_revenue"] == 100.0


def test_endpoint_generate_daily_report_with_date():
    """Test /generate-daily-report endpoint with specific date"""
    mock_sales = [
        {"event_id": "E1", "sale_date": "2025-09-15", "tickets_sold": 20, "revenue": 200.0}
    ]
    mock_names = {"E1": "Test Event"}
    
    with patch("src.report_service._query_daily_sales", return_value=mock_sales), \
         patch("src.report_service._query_event_names", return_value=mock_names), \
         patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 1}), \
         patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 3}):
        
        response = client.post("/generate-daily-report", json={
            "target_date": "2025-09-15",
            "output_format": "json"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report_date"] == "2025-09-15"
        assert ".json" in data["report_path"]
        assert data["summary"]["total_sales"] == 20


def test_endpoint_invalid_date_format():
    """Test /generate-daily-report endpoint with invalid date format"""
    response = client.post("/generate-daily-report", json={
        "target_date": "invalid-date"
    })
    
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Validation error"
    assert body["status_code"] == 422


def test_endpoint_invalid_output_format():
    """Test /generate-daily-report endpoint with invalid output format"""
    response = client.post("/generate-daily-report", json={
        "output_format": "xml"
    })
    
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Validation error"
    assert body["status_code"] == 422


def test_endpoint_database_error():
    """Test /generate-daily-report endpoint handles database errors"""
    with patch("src.report_service._query_daily_sales", side_effect=Exception("Database error")):
        response = client.post("/generate-daily-report", json={})
        
        assert response.status_code == 500
        assert "Report generation failed" in response.json()["detail"]


def test_report_includes_all_summary_fields(mock_db_data):
    """Test that generated report includes all required summary fields"""
    sales_data, event_names = mock_db_data
    
    with patch("src.report_service._query_daily_sales", return_value=sales_data), \
         patch("src.report_service._query_event_names", return_value=event_names), \
         patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 12}), \
         patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 7}):
        
        target_date = date(2025, 10, 4)
        report_path = generate_daily_report_csv(target_date=target_date, output_format="json")
        
        with open(report_path, "r") as f:
            data = json.load(f)
            
            # Check all required fields are present
            assert "report_date" in data
            assert "generated_at" in data
            assert "summary" in data
            assert "sales_by_event" in data
            
            # Check summary fields
            summary = data["summary"]
            assert "total_sales" in summary
            assert "total_revenue" in summary
            assert "total_transfers" in summary
            assert "invalid_scans" in summary
            
            # Verify values
            assert summary["total_sales"] == 80
            assert summary["total_revenue"] == 800.0
            assert summary["total_transfers"] == 12
            assert summary["invalid_scans"] == 7


def test_csv_report_structure(mock_db_data):
    """Test CSV report has correct structure"""
    sales_data, event_names = mock_db_data
    
    with patch("src.report_service._query_daily_sales", return_value=sales_data), \
         patch("src.report_service._query_event_names", return_value=event_names), \
         patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 0}), \
         patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 0}):
        
        target_date = date(2025, 10, 4)
        report_path = generate_daily_report_csv(target_date=target_date, output_format="csv")
        
        with open(report_path, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Check header rows
            assert rows[0][0] == "Daily Sales Report"
            
            # Check summary section exists
            assert any("Summary" in row[0] if row else False for row in rows)
            
            # Check detailed sales section exists
            assert any("Sales by Event" in row[0] if row else False for row in rows)
            
            # Check column headers for detailed section
            assert any("Event ID" in row[0] if row else False for row in rows)
