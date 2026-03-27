import base64
import json
import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from src.main import app
from src.config import get_settings

@pytest.fixture
def client(monkeypatch):
    """Fixture to provide a TestClient with a fixed signing key and cleared settings cache."""
    # Requirement: All tests must set QR_SIGNING_KEY to a 32-character test string
    monkeypatch.setenv("QR_SIGNING_KEY", "q" * 32)
    get_settings.cache_clear()
    return TestClient(app)

def test_qr_generate_validate_audit_flow(client):
    """
    End-to-end test for the QR lifecycle:
    1. Generate a signed QR token.
    2. Validate the token successfully.
    3. Validate a tampered token (invalid signature).
    4. Validate a token with extra fields (signature mismatch).
    5. Verify the audit log contains valid and invalid entries.
    6. Verify Prometheus metrics.
    """
    ticket_id = "E2E-TEST-001"
    event_name = "E2E-Festival"
    
    # --- Step 1: Generate QR ---
    gen_payload = {
        "ticket_id": ticket_id,
        "event": event_name,
        "user": "tester@example.com"
    }
    resp = client.post("/generate-qr", json=gen_payload)
    
    # Assertions 1 & 2: Status 200, valid PNG, and token presence
    assert resp.status_code == 200
    data = resp.json()
    assert "qr_base64" in data
    assert "token" in data  # Extracted signed token requirement
    
    qr_content = base64.b64decode(data["qr_base64"])
    assert qr_content.startswith(b"\x89PNG"), "QR code must be a PNG image"
    
    token_str = data["token"]
    token_obj = json.loads(token_str)
    
    # Store initial metrics
    def get_metric(res):
        return REGISTRY.get_sample_value("qr_validations_total", {"result": res}) or 0
    
    m_valid_start = get_metric("valid")
    m_invalid_start = get_metric("invalid")

    # --- Step 2: Validate (Successful) ---
    val_resp = client.post("/validate-qr", json={"qr_text": token_str})
    
    # Assertion 3: Valid scan returns True and correct metadata
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["isValid"] is True
    assert val_data["metadata"]["ticket_id"] == ticket_id
    assert val_data["metadata"]["event"] == event_name

    # --- Step 3: Validate (Tampered signature) ---
    tampered_token = token_obj.copy()
    tampered_token["sig"] = "invalid_signature_string"
    resp_tampered = client.post("/validate-qr", json={"qr_text": json.dumps(tampered_token)})
    
    # Assertion 4: Tampered signature returns False
    assert resp_tampered.status_code == 200
    assert resp_tampered.json()["isValid"] is False

    # --- Step 4: Validate (Extra field / Tampered payload) ---
    extra_field_token = token_obj.copy()
    extra_field_token["fraud"] = "injected"
    resp_extra = client.post("/validate-qr", json={"qr_text": json.dumps(extra_field_token)})
    
    # Assertion 5: Extra field (tampering) returns False
    assert resp_extra.status_code == 200
    assert resp_extra.json()["isValid"] is False

    # --- Step 5: Audit Log ---
    log_resp = client.get(f"/qr/scan-log/{ticket_id}")
    
    # Assertion 6: Audit log contains valid and invalid entries
    assert log_resp.status_code == 200
    logs = log_resp.json()
    assert len(logs) >= 2, "Should have at least one valid and one invalid log entry"
    
    has_valid = any(l["is_valid"] is True for l in logs)
    has_invalid = any(l["is_valid"] is False for l in logs)
    assert has_valid and has_invalid, "Audit log must contain both valid and invalid attempts"

    # --- Step 6: Prometheus Metrics ---
    # Assertion 7: Valid scan incremented counter
    assert get_metric("valid") == m_valid_start + 1
    
    # Assertion 8: Invalid scans incremented counter (2 invalid attempts in steps 3-4)
    assert get_metric("invalid") >= m_invalid_start + 2
