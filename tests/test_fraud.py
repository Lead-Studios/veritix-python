import os

os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_check_fraud_triggers_rules():
    # Too many purchases from same IP in 10min
    base_event = {
        "type": "purchase",
        "user": "user1",
        "ip": "1.2.3.4",
        "ticket_id": "T1",
        "timestamp": "2025-10-01T10:00:00",
    }
    events = [
        {**base_event, "timestamp": "2025-10-01T10:00:00"},
        {**base_event, "timestamp": "2025-10-01T10:01:00"},
        {**base_event, "timestamp": "2025-10-01T10:02:00"},
        {**base_event, "timestamp": "2025-10-01T10:03:00"},
    ]
    resp = client.post("/check-fraud", json={"events": events})
    assert resp.status_code == 200
    assert "too_many_purchases_same_ip" in resp.json()["triggered_rules"]


def test_check_fraud_duplicate_transfer():
    events = [
        {
            "type": "transfer",
            "user": "user2",
            "ip": "2.2.2.2",
            "ticket_id": "T2",
            "timestamp": "2025-10-01T11:00:00",
        },
        {
            "type": "transfer",
            "user": "user3",
            "ip": "2.2.2.2",
            "ticket_id": "T2",
            "timestamp": "2025-10-01T11:05:00",
        },
    ]
    resp = client.post("/check-fraud", json={"events": events})
    assert resp.status_code == 200
    assert "duplicate_ticket_transfer" in resp.json()["triggered_rules"]


def test_check_fraud_excessive_user_purchases():
    events = [
        {
            "type": "purchase",
            "user": "user4",
            "ip": "3.3.3.3",
            "ticket_id": f"T{i}",
            "timestamp": "2025-10-01T12:00:00",
        }
        for i in range(6)
    ]
    resp = client.post("/check-fraud", json={"events": events})
    assert resp.status_code == 200
    assert "excessive_purchases_user_day" in resp.json()["triggered_rules"]


def test_check_fraud_no_triggers():
    events = [
        {
            "type": "purchase",
            "user": "user5",
            "ip": "4.4.4.4",
            "ticket_id": "T10",
            "timestamp": "2025-10-01T13:00:00",
        },
        {
            "type": "transfer",
            "user": "user5",
            "ip": "4.4.4.4",
            "ticket_id": "T10",
            "timestamp": "2025-10-01T13:10:00",
        },
    ]
    resp = client.post("/check-fraud", json={"events": events})
    assert resp.status_code == 200
    assert resp.json()["triggered_rules"] == []