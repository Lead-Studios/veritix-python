import os
os.environ.setdefault("SKIP_MODEL_TRAINING", "true")
import httpx
import pytest
from src.main import app 
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_endpoint_status():
    response = client.get("/health")
    assert response.status_code == 200
    
def test_health_endpoint_content():
    response = client.get("/health")
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "OK"
    assert "service" in data
    assert data["service"] == "Veritix Backend"
