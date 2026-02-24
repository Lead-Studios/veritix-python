import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# --- IMPORTANT: Adjust these imports to match your project ---
# from src.main import app 
# from src.routers.analytics import summary_cache
# from src.database import get_db
# from src.auth import get_current_user
# -------------------------------------------------------------

# Mock setup for testing
from src.routers.analytics import summary_cache, router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

# Mocked Auth dependency override
def override_get_current_user():
    return {"id": 1, "username": "admin"}

app.dependency_overrides["get_current_user"] = override_get_current_user

client = TestClient(app)

def test_analytics_summary_caching(mocker):
    # 1. Clear the cache before the test starts
    summary_cache.clear()

    # 2. Mock the database session dependency
    mock_db = MagicMock()
    
    # Mocking the chained SQLAlchemy query results
    mock_query = MagicMock()
    mock_query.first.return_value = MagicMock(
        total_events=10, 
        total_tickets=150, 
        total_xlm=500.25, 
        total_usd=100.50
    )
    mock_query.scalar.return_value = "2026-01-01T12:00:00Z"
    
    mock_db.query.return_value = mock_query
    app.dependency_overrides["get_db"] = lambda: mock_db

    # 3. FIRST CALL - Should hit the mock database
    response1 = client.get("/analytics/summary")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["total_events"] == 10
    assert data1["total_revenue_usd"] == "100.5" # String validation check
    
    # Verify DB was queried (once for sales, once for ETL log)
    assert mock_db.query.call_count == 2

    # 4. SECOND CALL - Should return from Cache
    response2 = client.get("/analytics/summary")
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Verify the generated_at timestamp is IDENTICAL, proving it came from the cache
    assert data1["generated_at"] == data2["generated_at"]
    
    # Verify the DB was NOT called again (call count should still be 2)
    assert mock_db.query.call_count == 2