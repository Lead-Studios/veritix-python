# tests/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from app.main import app, manager
from datetime import datetime
import time
import threading
import json
import logging

@pytest.fixture
def client():
    return TestClient(app)

def _trigger_scan_via_post(client, scan):
    client.post("/scans", json=scan)

def test_websocket_receives_broadcast(client):
    scan = {
        "ticket_id": "TICKET-123",
        "event_id": "EVENT-1",
        "scanner_id": "GATE-A",
        "timestamp": datetime.utcnow().isoformat(),
        "meta": {"seat": "A1"}
    }

    with client.websocket_connect("/ws/ticket-scans") as websocket:
        # Start a thread that calls POST /scans after a short delay,
        # to simulate an external scan arriving while WS is open.
        t = threading.Timer(0.1, _trigger_scan_via_post, args=(client, scan))
        t.start()

        # Receive JSON message from websocket; timeout will raise if not received
        data = websocket.receive_json(timeout=5)
        # Verify payload contains expected fields
        assert data["ticket_id"] == scan["ticket_id"]
        assert data["event_id"] == scan["event_id"]
        assert data["meta"]["seat"] == "A1"
        t.cancel()

def test_connection_logging_is_emitted(client, caplog):
    caplog.set_level(logging.INFO)
    scan = {
        "ticket_id": "TICKET-888",
        "event_id": "EVENT-LOG",
        "timestamp": datetime.utcnow().isoformat(),
    }

    with client.websocket_connect("/ws/ticket-scans"):
        # When connection established, manager logs a connect message
        # Give small time for logger to emit
        time.sleep(0.05)
        # Ensure connect logged
        found_connect = any("WebSocket connected" in rec.message for rec in caplog.records)
        assert found_connect, "connect log not found; logs: %s" % [r.message for r in caplog.records]

    # After context manager exits, disconnect log should exist
    found_disconnect = any("WebSocket disconnected" in rec.message for rec in caplog.records)
    assert found_disconnect, "disconnect log not found; logs: %s" % [r.message for r in caplog.records]

    # Now connect again and trigger a scan; check broadcast log exists
    with client.websocket_connect("/ws/ticket-scans"):
        # trigger a scan
        client.post("/scans", json=scan)
        time.sleep(0.05)

    found_broadcast = any("Broadcasting scan" in rec.message or "Received scan for ticket_id" in rec.message for rec in caplog.records)
    assert found_broadcast, "broadcast not logged; logs: %s" % [r.message for r in caplog.records]
