import pytest
import time
from fastapi.testclient import TestClient
from src.main import app
from src.revenue_sharing_models import Stakeholder, EventRevenueInput
from src import calculation_history_store
from src.config import get_settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    """Ensure history table exists."""
    calculation_history_store.create_revenue_calculations_table()
    yield

def test_calculate_saves_to_history():
    """Test that POST /calculate-revenue-share saves a record in the background."""
    event_id = "history_event_1"
    input_data = {
        "event_id": event_id,
        "total_sales": 5000.0,
        "ticket_count": 50
    }
    
    # 1. Trigger calculation
    response = client.post("/calculate-revenue-share", json=input_data)
    assert response.status_code == 200
    
    # Needs a tiny bit of time for BackgroundTask to execute in TestClient
    # Though TestClient usually runs them synchronously, let's be safe.
    time.sleep(0.5)
    
    # 2. Check history
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}
    response = client.get(f"/revenue-share/history/{event_id}", headers=headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1
    assert history[0]["event_id"] == event_id
    assert history[0]["total_gross_sales"] == 5000.0
    assert "id" in history[0]

def test_get_history_pagination():
    """Test that history is paginated and ordered by date descending."""
    event_id = "paginated_event"
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}
    
    # Insert multiple records
    for i in range(3):
        input_data = {
            "event_id": event_id,
            "total_sales": 1000.0 + i,
            "ticket_count": 10
        }
        client.post("/calculate-revenue-share", json=input_data)
        time.sleep(1.1)  # Ensure distinct SQLite timestamps (1s precision)
    
    # Test limit=2
    response = client.get(f"/revenue-share/history/{event_id}?page=1&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Check descending order: 1002.0 should be first, then 1001.0
    assert data[0]["total_gross_sales"] == 1002.0
    assert data[1]["total_gross_sales"] == 1001.0

def test_get_calculation_by_id():
    """Test retrieving a specific calculation by ID."""
    event_id = "detail_event"
    input_data = {"event_id": event_id, "total_sales": 2000.0, "ticket_count": 20}
    client.post("/calculate-revenue-share", json=input_data)
    
    time.sleep(0.5)
    
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}
    
    # Get ID from history
    resp = client.get(f"/revenue-share/history/{event_id}", headers=headers)
    calc_id = resp.json()[0]["id"]
    
    # Get detail
    resp_detail = client.get(f"/revenue-share/history/{event_id}/{calc_id}", headers=headers)
    assert resp_detail.status_code == 200
    assert resp_detail.json()["id"] == calc_id
    assert resp_detail.json()["total_gross_sales"] == 2000.0
    assert isinstance(resp_detail.json()["distributions"], list)

def test_get_history_unauthorized():
    """Test that history routes require admin key."""
    event_id = "some_event"
    response = client.get(f"/revenue-share/history/{event_id}")
    assert response.status_code == 401 
