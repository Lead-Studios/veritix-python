import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_predict_scalper_returns_probability():
    payload = {"features": [3, 0.8, 1.1, 120, 0, 1]}
    response = client.post("/predict-scalper", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert isinstance(data["probability"], float)
    assert 0.0 <= data["probability"] <= 1.0


def test_predict_scalper_invalid_feature_length():
    payload = {"features": [1, 2, 3]}  # wrong length
    response = client.post("/predict-scalper", json=payload)
    # Model will raise due to shape; FastAPI returns 500 by default
    assert response.status_code in {400, 422, 500}

