import os
os.environ.setdefault("SKIP_MODEL_TRAINING", "true")
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


def test_generate_qr_success_returns_base64_png():
    payload = {"ticket_id": "ABC123", "event": "ConcertX", "user": "user_42"}
    response = client.post("/generate-qr", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "qr_base64" in data
    # Quick sanity check that it's decodable and looks like PNG
    import base64
    decoded = base64.b64decode(data["qr_base64"])  # should not raise
    assert isinstance(decoded, (bytes, bytearray))
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"  # PNG signature


def test_generate_qr_rejects_non_alphanumeric_ticket_id():
    payload = {"ticket_id": "INV@LID#", "event": "ConcertX", "user": "user_42"}
    response = client.post("/generate-qr", json=payload)
    assert response.status_code in {400, 422}


def test_validate_qr_roundtrip_validates_successfully():
    # First, generate a signed QR payload by calling the endpoint, then reconstruct the JSON used
    ticket = {"ticket_id": "TKT12345", "event": "Expo2025", "user": "alice"}
    gen = client.post("/generate-qr", json=ticket)
    assert gen.status_code == 200
    # Decode the PNG and extract the embedded JSON by re-encoding flow in app: we can't decode image here.
    # Instead, reproduce the signing locally via the app's helpers for a deterministic test input.
    from src.main import compute_signature
    unsigned = dict(ticket)
    qr_text = {
        **unsigned,
        "sig": compute_signature(unsigned)
    }
    res = client.post("/validate-qr", json={"qr_text": __import__("json").dumps(qr_text, separators=(",", ":"))})
    assert res.status_code == 200
    body = res.json()
    assert body["isValid"] is True
    assert body["metadata"]["ticket_id"] == ticket["ticket_id"]
    assert body["metadata"]["event"] == ticket["event"]
    assert body["metadata"]["user"] == ticket["user"]


def test_validate_qr_detects_tampered_payload():
    # Create a signed payload then tamper with a field
    from src.utils import compute_signature
    unsigned = {"ticket_id": "TKT987", "event": "ShowY", "user": "bob"}
    signed = {**unsigned, "sig": compute_signature(unsigned)}
    tampered = dict(signed)
    tampered["user"] = "mallory"
    res = client.post("/validate-qr", json={"qr_text": __import__("json").dumps(tampered, separators=(",", ":"))})
    assert res.status_code == 200
    body = res.json()
    assert body["isValid"] is False

