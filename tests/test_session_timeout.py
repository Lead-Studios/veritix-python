"""Tests for WebSocket session timeout functionality."""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app, manager
from app.manager import TicketScanManager


@pytest.fixture
def test_manager():
    """Create a test manager with short timeout for testing."""
    return TicketScanManager(session_timeout_minutes=1)  # 1 minute for testing


@pytest.fixture
def client():
    return TestClient(app)


def test_manager_initialization():
    """Test that manager initializes with correct timeout."""
    mgr = TicketScanManager(session_timeout_minutes=30)
    assert mgr.session_timeout == timedelta(minutes=30)
    assert len(mgr.active_connections) == 0
    assert len(mgr.connection_activity) == 0


@pytest.mark.asyncio
async def test_connect_updates_activity_time(test_manager):
    """Test that connect method updates activity timestamp."""
    mock_ws = AsyncMock()
    
    await test_manager.connect(mock_ws)
    
    assert mock_ws in test_manager.active_connections
    assert mock_ws in test_manager.connection_activity
    assert isinstance(test_manager.connection_activity[mock_ws], datetime)


@pytest.mark.asyncio
async def test_disconnect_removes_connection_and_activity(test_manager):
    """Test that disconnect method removes both connection and activity tracking."""
    mock_ws = AsyncMock()
    
    # First connect
    await test_manager.connect(mock_ws)
    assert mock_ws in test_manager.active_connections
    assert mock_ws in test_manager.connection_activity
    
    # Then disconnect
    await test_manager.disconnect(mock_ws)
    assert mock_ws not in test_manager.active_connections
    assert mock_ws not in test_manager.connection_activity


@pytest.mark.asyncio
async def test_cleanup_inactive_sessions_removes_expired_connections(test_manager):
    """Test that inactive sessions are cleaned up."""
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    
    # Connect both clients
    await test_manager.connect(mock_ws1)
    await test_manager.connect(mock_ws2)
    
    assert len(test_manager.active_connections) == 2
    assert len(test_manager.connection_activity) == 2
    
    # Manually set one connection to be expired (1 hour old)
    expired_time = datetime.utcnow() - timedelta(hours=1)
    test_manager.connection_activity[mock_ws1] = expired_time
    
    # Run cleanup once
    await test_manager._cleanup_inactive_sessions()
    
    # Only the expired connection should be removed
    assert mock_ws1 not in test_manager.active_connections
    assert mock_ws1 not in test_manager.connection_activity
    assert mock_ws2 in test_manager.active_connections
    assert mock_ws2 in test_manager.connection_activity
    assert len(test_manager.active_connections) == 1


@pytest.mark.asyncio
async def test_cleanup_task_lifecycle():
    """Test that cleanup task can be started and stopped."""
    mgr = TicketScanManager(session_timeout_minutes=1)
    
    # Start task
    await mgr.start_cleanup_task()
    assert mgr._cleanup_task is not None
    assert not mgr._cleanup_task.done()
    
    # Stop task
    await mgr.stop_cleanup_task()
    assert mgr._cleanup_task is None


@pytest.mark.asyncio
async def test_broadcast_updates_activity_for_all_connections(test_manager):
    """Test that broadcast updates activity time for all connections."""
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    
    # Connect clients
    await test_manager.connect(mock_ws1)
    await test_manager.connect(mock_ws2)
    
    # Store initial activity times
    initial_time_1 = test_manager.connection_activity[mock_ws1]
    initial_time_2 = test_manager.connection_activity[mock_ws2]
    
    # Broadcast a message
    await test_manager.broadcast_scan({"test": "data"})
    
    # Activity times should be updated (newer)
    assert test_manager.connection_activity[mock_ws1] > initial_time_1
    assert test_manager.connection_activity[mock_ws2] > initial_time_2


@pytest.mark.asyncio
async def test_session_timeout_config_from_environment():
    """Test that session timeout can be configured via environment variable."""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.return_value = "45"  # 45 minutes
        
        # Import after patching
        import importlib
        import app.main
        importlib.reload(app.main)
        
        # Create new manager with patched environment
        mgr = app.main.manager
        assert mgr.session_timeout == timedelta(minutes=45)


def test_websocket_endpoint_accepts_connections(client):
    """Test that WebSocket endpoint accepts connections."""
    with client.websocket_connect("/ws/ticket-scans") as websocket:
        # Connection should be established
        assert websocket is not None


@pytest.mark.asyncio
async def test_cleanup_handles_exceptions_gracefully(test_manager):
    """Test that cleanup task continues running even if exceptions occur."""
    # Mock datetime to simulate time passing
    with patch('app.manager.datetime') as mock_datetime:
        # Set up initial time
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = start_time
        mock_datetime.side_effect = lambda: mock_datetime.utcnow.return_value
        
        mock_ws = AsyncMock()
        await test_manager.connect(mock_ws)
        
        # Make connection appear expired
        mock_datetime.utcnow.return_value = start_time + timedelta(minutes=2)
        
        # This should not raise an exception
        await test_manager._cleanup_inactive_sessions()
        
        # Connection should be removed
        assert mock_ws not in test_manager.active_connections


@pytest.mark.asyncio
async def test_multiple_broadcasts_update_activity(test_manager):
    """Test that multiple broadcasts keep updating activity times."""
    mock_ws = AsyncMock()
    await test_manager.connect(mock_ws)
    
    initial_time = test_manager.connection_activity[mock_ws]
    
    # Multiple broadcasts
    await test_manager.broadcast_scan({"msg": "1"})
    time_after_first = test_manager.connection_activity[mock_ws]
    
    await test_manager.broadcast_scan({"msg": "2"})
    time_after_second = test_manager.connection_activity[mock_ws]
    
    # Each broadcast should update the timestamp
    assert time_after_first > initial_time
    assert time_after_second > time_after_first