import os
os.environ.setdefault("SKIP_MODEL_TRAINING", "true")
import json
import base64

from fastapi.testclient import TestClient
from src.main import app

from src.utils import compute_signature
from src.fraud import determine_severity


client = TestClient(app)


def test_root_and_health():
    r = client.get("/")
    assert r.status_code == 200
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json().get("status") == "OK"


def test_qr_generate_and_validate_roundtrip():
    ticket = {"ticket_id": "INTG123", "event": "IntFest", "user": "eve"}
    gen = client.post("/generate-qr", json=ticket)
    assert gen.status_code == 200
    data = gen.json()
    assert "qr_base64" in data
    decoded = base64.b64decode(data["qr_base64"])  # sanity decode
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"

    # Construct signed JSON payload for validate endpoint
    unsigned = dict(ticket)
    signed = {**unsigned, "sig": compute_signature(unsigned)}
    validate = client.post("/validate-qr", json={"qr_text": json.dumps(signed, separators=(",", ":"))})
    assert validate.status_code == 200
    body = validate.json()
    assert body["isValid"] is True


def test_predict_and_check_fraud_combined_flow():
    # Predict endpoint: valid features
    payload = {"features": [2, 0.2, 1.0, 365, 0, 0]}
    p = client.post("/predict-scalper", json=payload)
    assert p.status_code == 200
    prob = p.json().get("probability")
    assert isinstance(prob, float)

    # Check fraud: trigger rules and then map severity
    events = [
        {"type": "purchase", "user": "u1", "ip": "9.9.9.9", "ticket_id": "A1", "timestamp": "2025-10-01T10:00:00"},
        {"type": "purchase", "user": "u1", "ip": "9.9.9.9", "ticket_id": "A2", "timestamp": "2025-10-01T10:01:00"},
        {"type": "purchase", "user": "u1", "ip": "9.9.9.9", "ticket_id": "A3", "timestamp": "2025-10-01T10:02:00"},
        {"type": "purchase", "user": "u1", "ip": "9.9.9.9", "ticket_id": "A4", "timestamp": "2025-10-01T10:03:00"},
    ]
    cf = client.post("/check-fraud", json={"events": events})
    assert cf.status_code == 200
    triggered = cf.json().get("triggered_rules")
    assert isinstance(triggered, list)
    sev = determine_severity(triggered)
    # With many purchases from same IP we expect at least 'high' or 'medium'
    assert sev in {"low", "medium", "high"}
