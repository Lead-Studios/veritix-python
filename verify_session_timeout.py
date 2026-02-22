#!/usr/bin/env python3
"""
Simple test script to verify session timeout functionality without pytest dependencies.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from manager import TicketScanManager
from datetime import datetime, timedelta
from unittest.mock import AsyncMock


async def test_basic_functionality():
    """Test basic session timeout functionality."""
    print("Testing basic session timeout functionality...")
    
    # Create manager with 1 minute timeout
    manager = TicketScanManager(session_timeout_minutes=1)
    
    # Test 1: Initialization
    assert manager.session_timeout == timedelta(minutes=1)
    assert len(manager.active_connections) == 0
    assert len(manager.connection_activity) == 0
    print("✓ Manager initialization correct")
    
    # Test 2: Connect updates activity
    mock_ws = AsyncMock()
    await manager.connect(mock_ws)
    
    assert mock_ws in manager.active_connections
    assert mock_ws in manager.connection_activity
    assert isinstance(manager.connection_activity[mock_ws], datetime)
    print("✓ Connect method updates activity tracking")
    
    # Test 3: Disconnect removes tracking
    await manager.disconnect(mock_ws)
    
    assert mock_ws not in manager.active_connections
    assert mock_ws not in manager.connection_activity
    print("✓ Disconnect method removes tracking")
    
    # Test 4: Cleanup task lifecycle
    await manager.start_cleanup_task()
    assert manager._cleanup_task is not None
    assert not manager._cleanup_task.done()
    print("✓ Cleanup task started successfully")
    
    await manager.stop_cleanup_task()
    assert manager._cleanup_task is None
    print("✓ Cleanup task stopped successfully")
    
    print("\nAll basic tests passed! ✅")


async def test_timeout_logic():
    """Test timeout logic with manual time manipulation."""
    print("\nTesting timeout logic...")
    
    manager = TicketScanManager(session_timeout_minutes=1)
    mock_ws = AsyncMock()
    
    # Connect client
    await manager.connect(mock_ws)
    initial_time = manager.connection_activity[mock_ws]
    
    # Test that connection is active
    assert len(manager.active_connections) == 1
    print("✓ Connection established")
    
    # Test broadcast updates activity
    await manager.broadcast_scan({"test": "message"})
    updated_time = manager.connection_activity[mock_ws]
    
    assert updated_time > initial_time
    print("✓ Broadcast updates activity timestamp")
    
    # Test cleanup with expired connection
    # Manually set connection to be expired
    expired_time = datetime.utcnow() - timedelta(minutes=2)
    manager.connection_activity[mock_ws] = expired_time
    
    # Run cleanup
    await manager._cleanup_inactive_sessions()
    
    # Connection should be removed
    assert mock_ws not in manager.active_connections
    assert mock_ws not in manager.connection_activity
    print("✓ Inactive connections are cleaned up")
    
    print("\nTimeout logic tests passed! ✅")


if __name__ == "__main__":
    print("Running session timeout verification tests...\n")
    
    try:
        asyncio.run(test_basic_functionality())
        asyncio.run(test_timeout_logic())
        print("\n🎉 All tests passed successfully!")
        print("\nSession timeout feature is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)