import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.ratelimit import limiter

client = TestClient(app)

@pytest.fixture(autouse=True)
def enable_limiter_for_test():
    """Force the limiter to be enabled just for this test file, and clear it after."""
    limiter.enabled = True
    limiter._storage.reset() # Reset in-memory counters
    yield
    limiter._storage.reset()
    limiter.enabled = False # Return to default test state

def test_qr_verify_rate_limit():
    # 1. Hit the endpoint up to the limit (30 requests)
    for _ in range(30):
        response = client.post("/qr/verify")
        assert response.status_code == 200

    # 2. The 31st request should trigger the 429 Rate Limit Exceeded
    response_429 = client.post("/qr/verify")
    
    assert response_429.status_code == 429
    data = response_429.json()
    
    assert data["success"] is False
    assert "Rate limit exceeded" in data["error"]

def test_qr_generate_rate_limit(mocker):
    # Mock the auth dependency so we can test the rate limit directly
    from src.auth.dependencies import require_service_key
    app.dependency_overrides[require_service_key] = lambda: "mocked_token"
    
    # 1. Hit the endpoint up to the limit (60 requests)
    for _ in range(60):
        response = client.post("/qr/generate")
        assert response.status_code == 200

    # 2. The 61st request should trigger the 429
    response_429 = client.post("/qr/generate")
    assert response_429.status_code == 429
    
    # Clean up overrides
    app.dependency_overrides.clear()