from fastapi.testclient import TestClient  
from src.main import app  

client = TestClient(app)  

def test_recommend_events_valid_user():  
    response = client.post("/recommend-events", json={"user_id": "user1"})  
    assert response.status_code == 200  
    data = response.json()  
    assert "recommendations" in data  
    assert isinstance(data["recommendations"], list)  
    assert len(data["recommendations"]) <= 3  

def test_recommend_events_cold_start_unknown_user():
    """Unknown user gets cold-start recommendations (most popular events), not 404."""
    response = client.post("/recommend-events", json={"user_id": "unknown"})
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) <= 3