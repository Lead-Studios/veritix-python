"""Unit tests for analytics module."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.analytics.service import AnalyticsService
from src.analytics.models import (
    TicketScan, TicketTransfer, InvalidAttempt, AnalyticsStats,
    init_db
)


class TestAnalyticsService:
    """Test the analytics service."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Initialize database tables
        init_db()
        self.service = AnalyticsService()
    
    def test_log_ticket_scan(self):
        """Test logging a ticket scan."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock the session operations
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            
            # Call the method
            self.service.log_ticket_scan(
                ticket_id="ticket_123",
                event_id="event_456",
                scanner_id="scanner_789",
                is_valid=True,
                location="Venue A",
                device_info="iPhone iOS 15"
            )
            
            # Verify session was used correctly
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_log_ticket_transfer(self):
        """Test logging a ticket transfer."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock the session operations
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            
            # Call the method
            self.service.log_ticket_transfer(
                ticket_id="ticket_123",
                event_id="event_456",
                from_user_id="user_abc",
                to_user_id="user_def",
                transfer_reason="gift",
                ip_address="192.168.1.1",
                is_successful=True
            )
            
            # Verify session was used correctly
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_log_invalid_attempt(self):
        """Test logging an invalid attempt."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock the session operations
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            
            # Call the method
            self.service.log_invalid_attempt(
                attempt_type="scan",
                ticket_id="ticket_123",
                event_id="event_456",
                reason="invalid_qr",
                ip_address="192.168.1.1"
            )
            
            # Verify session was used correctly
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_get_stats_for_event_existing(self):
        """Test getting stats for an existing event."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock the query result
            mock_stats = MagicMock()
            mock_stats.event_id = "event_456"
            mock_stats.scan_count = 10
            mock_stats.transfer_count = 5
            mock_stats.invalid_attempt_count = 2
            mock_stats.valid_scan_count = 8
            mock_stats.invalid_scan_count = 2
            mock_stats.successful_transfer_count = 4
            mock_stats.failed_transfer_count = 1
            mock_stats.stat_date = datetime.utcnow()
            
            mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_stats
            
            result = self.service.get_stats_for_event("event_456")
            
            assert result["event_id"] == "event_456"
            assert result["scan_count"] == 10
            assert result["transfer_count"] == 5
            assert result["invalid_attempt_count"] == 2
    
    def test_get_stats_for_event_new(self):
        """Test getting stats for a new event (calculate from raw data)."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock empty stats query result
            mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            
            # Mock counts for raw data
            mock_query = MagicMock()
            mock_query.count.return_value = 10  # scan count
            mock_session.query.return_value.filter.return_value = mock_query
            
            # Mock valid scan count
            mock_valid_query = MagicMock()
            mock_valid_query.count.return_value = 8
            mock_session.query.return_value.filter.return_value.filter.return_value = mock_valid_query
            
            # Mock transfer count
            mock_transfer_query = MagicMock()
            mock_transfer_query.count.return_value = 5
            mock_session.query.return_value.filter.return_value = mock_transfer_query
            
            # Mock successful transfer count
            mock_success_transfer_query = MagicMock()
            mock_success_transfer_query.count.return_value = 4
            mock_session.query.return_value.filter.return_value.filter.return_value = mock_success_transfer_query
            
            # Mock invalid attempt count
            mock_invalid_query = MagicMock()
            mock_invalid_query.count.return_value = 2
            mock_session.query.return_value.filter.return_value = mock_invalid_query
            
            result = self.service.get_stats_for_event("event_456")
            
            assert result["event_id"] == "event_456"
            assert result["scan_count"] == 10
            assert result["transfer_count"] == 5
            assert result["invalid_attempt_count"] == 2
            assert result["valid_scan_count"] == 8
            assert result["invalid_scan_count"] == 2
            assert result["successful_transfer_count"] == 4
            assert result["failed_transfer_count"] == 1
    
    def test_get_stats_for_all_events(self):
        """Test getting stats for all events."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock distinct event IDs
            mock_ticket_scan_result = [("event_456",)]
            mock_transfer_result = [("event_789",)]
            mock_invalid_result = [("event_abc",)]
            
            mock_session.query.return_value.distinct.return_value.all.return_value = mock_ticket_scan_result
            mock_session.query.return_value.distinct.return_value.all.return_value = mock_transfer_result
            mock_session.query.return_value.distinct.return_value.all.return_value = mock_invalid_result
            
            # Mock the get_stats_for_event method to return test data
            with patch.object(self.service, 'get_stats_for_event') as mock_get_stats:
                mock_get_stats.side_effect = lambda event_id: {
                    "event_id": event_id,
                    "scan_count": 10 if event_id == "event_456" else 5,
                    "transfer_count": 5 if event_id == "event_456" else 3,
                    "invalid_attempt_count": 2 if event_id == "event_456" else 1
                }
                
                result = self.service.get_stats_for_all_events()
                
                # Should have stats for all unique events
                assert len(result) == 3
                assert "event_456" in result
                assert "event_789" in result
                assert "event_abc" in result
    
    def test_get_recent_scans(self):
        """Test getting recent scans for an event."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock scan records
            mock_scan = MagicMock()
            mock_scan.id = 1
            mock_scan.ticket_id = "ticket_123"
            mock_scan.scanner_id = "scanner_456"
            mock_scan.scan_timestamp = datetime.utcnow()
            mock_scan.is_valid = True
            mock_scan.location = "Gate A"
            
            mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_scan]
            
            result = self.service.get_recent_scans("event_456", 10)
            
            assert len(result) == 1
            assert result[0]["ticket_id"] == "ticket_123"
            assert result[0]["is_valid"] is True
    
    def test_get_recent_transfers(self):
        """Test getting recent transfers for an event."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock transfer records
            mock_transfer = MagicMock()
            mock_transfer.id = 1
            mock_transfer.ticket_id = "ticket_123"
            mock_transfer.from_user_id = "user_abc"
            mock_transfer.to_user_id = "user_def"
            mock_transfer.transfer_timestamp = datetime.utcnow()
            mock_transfer.is_successful = True
            mock_transfer.transfer_reason = "gift"
            
            mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_transfer]
            
            result = self.service.get_recent_transfers("event_456", 10)
            
            assert len(result) == 1
            assert result[0]["ticket_id"] == "ticket_123"
            assert result[0]["is_successful"] is True
    
    def test_get_invalid_attempts(self):
        """Test getting invalid attempts for an event."""
        with patch('src.analytics.service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock invalid attempt records
            mock_attempt = MagicMock()
            mock_attempt.id = 1
            mock_attempt.attempt_type = "scan"
            mock_attempt.ticket_id = "ticket_123"
            mock_attempt.attempt_timestamp = datetime.utcnow()
            mock_attempt.reason = "invalid_qr"
            mock_attempt.ip_address = "192.168.1.1"
            
            mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_attempt]
            
            result = self.service.get_invalid_attempts("event_456", 10)
            
            assert len(result) == 1
            assert result[0]["attempt_type"] == "scan"
            assert result[0]["reason"] == "invalid_qr"


def test_ticket_scan_model():
    """Test TicketScan model."""
    scan = TicketScan(
        ticket_id="ticket_123",
        event_id="event_456",
        scanner_id="scanner_789",
        is_valid=True,
        location="Venue A",
        device_info="iPhone iOS 15"
    )
    
    assert scan.ticket_id == "ticket_123"
    assert scan.event_id == "event_456"
    assert scan.is_valid is True
    assert scan.location == "Venue A"


def test_ticket_transfer_model():
    """Test TicketTransfer model."""
    transfer = TicketTransfer(
        ticket_id="ticket_123",
        event_id="event_456",
        from_user_id="user_abc",
        to_user_id="user_def",
        transfer_reason="gift",
        is_successful=True
    )
    
    assert transfer.ticket_id == "ticket_123"
    assert transfer.event_id == "event_456"
    assert transfer.from_user_id == "user_abc"
    assert transfer.to_user_id == "user_def"
    assert transfer.is_successful is True


def test_invalid_attempt_model():
    """Test InvalidAttempt model."""
    attempt = InvalidAttempt(
        attempt_type="scan",
        ticket_id="ticket_123",
        event_id="event_456",
        reason="invalid_qr"
    )
    
    assert attempt.attempt_type == "scan"
    assert attempt.ticket_id == "ticket_123"
    assert attempt.event_id == "event_456"
    assert attempt.reason == "invalid_qr"


def test_analytics_stats_model():
    """Test AnalyticsStats model."""
    stats = AnalyticsStats(
        event_id="event_456",
        scan_count=10,
        transfer_count=5,
        invalid_attempt_count=2
    )
    
    assert stats.event_id == "event_456"
    assert stats.scan_count == 10
    assert stats.transfer_count == 5
    assert stats.invalid_attempt_count == 2


def test_database_functions():
    """Test database utility functions."""
    from src.analytics.models import get_database_url, get_engine
    
    # Test default SQLite URL
    db_url = get_database_url()
    assert db_url.endswith("analytics.db")
    
    # Test engine creation
    engine = get_engine()
    assert engine is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])