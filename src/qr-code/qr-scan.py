import json
import os
import pytest
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.middleware.logging import RequestLoggingMiddleware, logger

# Create a clean test app
app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/test")
def test_route():
    return {"msg": "success"}

client = TestClient(app)

def test_request_logging_standard_route(caplog):
    # Set caplog to capture INFO level logs from our specific logger
    caplog.set_level(logging.INFO, logger="api.request_logger")
    
    response = client.get("/api/test")
    assert response.status_code == 200

    # Ensure a log was created
    assert len(caplog.records) == 1
    
    # Parse the JSON log
    log_record = json.loads(caplog.records[0].message)
    
    assert log_record["method"] == "GET"
    assert log_record["path"] == "/api/test"
    assert log_record["status"] == 200
    assert "duration_ms" in log_record
    assert "timestamp" in log_record
    assert "headers" not in log_record  # Not in debug mode by default

def test_request_logging_excludes_health(caplog):
    caplog.set_level(logging.INFO, logger="api.request_logger")
    
    response = client.get("/health")
    assert response.status_code == 200

    # Ensure no logs were created for the health endpoint
    assert len(caplog.records) == 0

def test_request_logging_debug_mode_headers(caplog, monkeypatch):
    # Force DEBUG mode on
    monkeypatch.setenv("DEBUG", "true")
    caplog.set_level(logging.INFO, logger="api.request_logger")
    
    headers = {
        "X-Custom-Header": "TestValue",
        "Authorization": "Bearer secret_token_do_not_log"
    }
    
    response = client.get("/api/test", headers=headers)
    assert response.status_code == 200

    assert len(caplog.records) == 1
    log_record = json.loads(caplog.records[0].message)
    
    # Check that headers were included in DEBUG mode
    assert "headers" in log_record
    
    # Ensure safe headers are present
    assert log_record["headers"]["x-custom-header"] == "TestValue"
    
    # Ensure Authorization is STRIPPED
    assert "authorization" not in log_record["headers"]