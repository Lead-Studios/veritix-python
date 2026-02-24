import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from src.auth.dependencies import require_service_key, require_admin_key
from src.config import settings

# Setup a dummy FastAPI app for isolated auth testing
app = FastAPI()

@app.get("/service-protected", dependencies=[Depends(require_service_key)])
def service_route():
    return {"msg": "service success"}

@app.get("/admin-protected", dependencies=[Depends(require_admin_key)])
def admin_route():
    return {"msg": "admin success"}

client = TestClient(app)

def test_missing_token():
    # Test Service Route
    response = client.get("/service-protected")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid authentication token"
    
    # Test Admin Route
    response = client.get("/admin-protected")
    assert response.status_code == 401

def test_invalid_token():
    headers = {"Authorization": "Bearer completely_wrong_token"}
    
    # Test Service Route
    response = client.get("/service-protected", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid service token"
    
    # Test Admin Route
    response = client.get("/admin-protected", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin token"

def test_valid_service_token():
    headers = {"Authorization": f"Bearer {settings.SERVICE_API_KEY}"}
    response = client.get("/service-protected", headers=headers)
    assert response.status_code == 200
    assert response.json()["msg"] == "service success"

def test_valid_admin_token():
    headers = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}
    response = client.get("/admin-protected", headers=headers)
    assert response.status_code == 200
    assert response.json()["msg"] == "admin success"

def test_cross_auth_fails():
    """Ensure a valid service token cannot access an admin route and vice-versa."""
    service_headers = {"Authorization": f"Bearer {settings.SERVICE_API_KEY}"}
    admin_headers = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}
    
    response1 = client.get("/admin-protected", headers=service_headers)
    assert response1.status_code == 403
    
    response2 = client.get("/service-protected", headers=admin_headers)
    assert response2.status_code == 403