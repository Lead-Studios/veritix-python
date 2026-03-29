import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.revenue_sharing_models import Stakeholder, EventRevenueInput
from src import stakeholder_store
from src.config import get_settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    """Ensure stakeholders table exists and is clean for each test."""
    stakeholder_store.create_stakeholders_table()
    # No easy way to 'clean' without raw SQL here, but we'll use unique event IDs
    yield

def test_get_stakeholders_fallback():
    """Test that it falls back to defaults when no DB record exists."""
    event_id = "non_existent_event_999"
    response = client.get(f"/revenue-share/stakeholders/{event_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(s["role"] == "organizer" for s in data)
    assert any(s["role"] == "platform" for s in data)
    assert any(s["role"] == "venue" for s in data)

def test_save_and_get_stakeholders_api():
    """Test saving custom stakeholders via API and retrieving them."""
    event_id = "custom_event_123"
    custom_stakeholders = [
        {
            "id": "stakeholder_1",
            "name": "Custom Artist",
            "role": "artist",
            "percentage": 50.0,
            "payment_address": "0xArtist"
        },
        {
            "id": "stakeholder_2",
            "name": "Custom Organizer",
            "role": "organizer",
            "percentage": 50.0,
            "payment_address": "0xOrganizer"
        }
    ]
    
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}
    
    # Save custom stakeholders
    response = client.post(
        f"/revenue-share/stakeholders/{event_id}",
        json=custom_stakeholders,
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Retrieve them
    response = client.get(f"/revenue-share/stakeholders/{event_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["role"] == "artist"
    assert data[0]["percentage"] == 50.0
    assert data[1]["role"] == "organizer"
    assert data[1]["percentage"] == 50.0

def test_calculate_revenue_shares_uses_persistence():
    """Test that revenue calculation uses stakeholders from the database."""
    event_id = "persistent_event_456"
    custom_stakeholders = [
        Stakeholder(
            id="p_stakeholder_1",
            name="Mega Artist",
            role="artist",
            percentage=90.0
        ),
        Stakeholder(
            id="p_stakeholder_2",
            name="Tiny Organizer",
            role="organizer",
            percentage=10.0
        )
    ]
    
    # Save directly to store to avoid API auth overhead in this logic test
    stakeholder_store.save_stakeholders_for_event(event_id, custom_stakeholders)
    
    # Calculate revenue share
    input_data = {
        "event_id": event_id,
        "total_sales": 1000.0,
        "ticket_count": 10
    }
    response = client.post("/calculate-revenue-share", json=input_data)
    assert response.status_code == 200
    result = response.json()
    
    # Verify distributions match custom stakeholders
    distributions = result["distributions"]
    assert len(distributions) == 2
    # The roles might be used for matching in the service, let's check
    roles = [d["role"] for d in distributions]
    assert "artist" in roles
    assert "organizer" in roles
    
    artist_dist = next(d for d in distributions if d["role"] == "artist")
    assert artist_dist["percentage_applied"] == 90.0

def test_save_stakeholders_unauthorized():
    """Test that saving stakeholders requires admin key."""
    event_id = "secret_event"
    response = client.post(f"/revenue-share/stakeholders/{event_id}", json=[])
    assert response.status_code == 401  # Unauthorized without Bearer token
