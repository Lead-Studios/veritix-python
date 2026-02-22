"""Tests for structured logging and Prometheus metrics functionality."""
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.logging_config import (
    JSONFormatter, RequestIDMiddleware, MetricsMiddleware,
    setup_logging, log_info, log_error, log_warning
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    with patch('src.logging_config.logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


class TestJSONFormatter:
    """Test JSON logging formatter."""
    
    def test_format_with_request_id(self):
        """Test formatting with request ID context."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Test with request ID context
        with patch('src.logging_config.request_id_context') as mock_context:
            mock_context.get.return_value = 'test-request-id'
            result = formatter.format(record)
            
            parsed = json.loads(result)
            assert parsed['message'] == 'Test message'
            assert parsed['level'] == 'INFO'
            assert parsed['request_id'] == 'test-request-id'
            assert 'timestamp' in parsed
    
    def test_format_with_extra_data(self):
        """Test formatting with extra data."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.extra_data = {'key': 'value', 'number': 42}
        
        with patch('src.logging_config.request_id_context') as mock_context:
            mock_context.get.return_value = 'test-request-id'
            result = formatter.format(record)
            
            parsed = json.loads(result)
            assert parsed['key'] == 'value'
            assert parsed['number'] == 42


class TestRequestIDMiddleware:
    """Test request ID middleware."""
    
    @pytest.mark.asyncio
    async def test_request_id_generation(self):
        """Test that request IDs are generated and added to headers."""
        middleware = RequestIDMiddleware(app)
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.method = 'GET'
        mock_request.url.path = '/test'
        mock_request.headers = {}
        mock_request.client.host = '127.0.0.1'
        
        # Mock call_next to return a response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        with patch('src.logging_config.time.time', side_effect=[0, 1]):  # 1 second duration
            with patch('src.logging_config.log_info') as mock_log:
                response = await middleware.dispatch(mock_request, lambda req: mock_response)
                
                # Check that request ID was added to response headers
                assert 'X-Request-ID' in response.headers
                assert len(response.headers['X-Request-ID']) > 0
                
                # Check that log was called with request info
                mock_log.assert_called_once()
                call_args = mock_log.call_args[0]
                assert 'Request completed' in call_args[0]
    
    def test_get_client_ip_with_forwarded_headers(self):
        """Test client IP extraction with forwarded headers."""
        middleware = RequestIDMiddleware(app)
        
        mock_request = MagicMock()
        mock_request.headers = {
            'x-forwarded-for': '192.168.1.1, 10.0.0.1',
            'x-real-ip': '192.168.1.1'
        }
        mock_request.client = MagicMock()
        mock_request.client.host = '127.0.0.1'
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == '192.168.1.1'
    
    def test_get_client_ip_without_forwarded_headers(self):
        """Test client IP extraction without forwarded headers."""
        middleware = RequestIDMiddleware(app)
        
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = '192.168.1.100'
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == '192.168.1.100'


class TestMetricsMiddleware:
    """Test metrics middleware."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test that metrics are collected for requests."""
        middleware = MetricsMiddleware(app)
        
        mock_request = MagicMock()
        mock_request.method = 'GET'
        mock_request.url.path = '/test'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('src.logging_config.time.time', side_effect=[0, 0.1]):  # 100ms duration
            with patch('src.logging_config.REQUEST_COUNT') as mock_counter:
                with patch('src.logging_config.REQUEST_DURATION') as mock_histogram:
                    with patch('src.logging_config.REQUEST_IN_PROGRESS') as mock_gauge:
                        await middleware.dispatch(mock_request, lambda req: mock_response)
                        
                        # Check that metrics were updated
                        mock_counter.labels().inc.assert_called_once()
                        mock_histogram.labels().observe.assert_called_once_with(0.1)
                        mock_gauge.labels().inc.assert_called_once()
                        mock_gauge.labels().dec.assert_called_once()


class TestLoggingFunctions:
    """Test logging convenience functions."""
    
    def test_log_info(self, mock_logger):
        """Test info logging function."""
        log_info('Test info message', {'key': 'value'})
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == 'Test info message'
        assert 'extra' in call_args[1]
        assert call_args[1]['extra']['extra_data']['key'] == 'value'
    
    def test_log_error(self, mock_logger):
        """Test error logging function."""
        log_error('Test error message', {'error': 'test'})
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == 'Test error message'
        assert 'extra' in call_args[1]
        assert call_args[1]['extra']['extra_data']['error'] == 'test'
    
    def test_log_warning(self, mock_logger):
        """Test warning logging function."""
        log_warning('Test warning message', {'warning': 'test'})
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[0][0] == 'Test warning message'
        assert 'extra' in call_args[1]
        assert call_args[1]['extra']['extra_data']['warning'] == 'test'


class TestEndpoints:
    """Test that endpoints generate proper logs and metrics."""
    
    def test_health_endpoint(self, client):
        """Test health endpoint logging."""
        with patch('src.logging_config.log_info') as mock_log:
            response = client.get('/health')
            assert response.status_code == 200
            
            # Check that log was called
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert 'Health check requested' in call_args[0]
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        with patch('src.logging_config.log_info') as mock_log:
            response = client.get('/metrics')
            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/plain; version=0.0.4; charset=utf-8'
            
            # Check that log was called
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert 'Metrics endpoint requested' in call_args[0]
    
    def test_predict_scalper_endpoint(self, client):
        """Test predict scalper endpoint logging."""
        with patch('src.logging_config.log_info') as mock_log:
            response = client.post('/predict-scalper', json={
                'features': [1.0, 2.0, 3.0]
            })
            # May return 503 if model not ready, but logging should still occur
            mock_log.assert_called()
    
    def test_generate_qr_endpoint(self, client):
        """Test QR generation endpoint logging."""
        with patch('src.logging_config.log_info') as mock_log:
            with patch('src.logging_config.log_warning') as mock_warn:
                response = client.post('/generate-qr', json={
                    'ticket_id': 'test-ticket',
                    'event': 'test-event',
                    'user': 'test-user'
                })
                # May return 500 if qrcode not installed, but logging should occur
                assert mock_log.called or mock_warn.called


def test_setup_logging():
    """Test logging setup function."""
    with patch('src.logging_config.logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging('DEBUG')
        
        # Check that logger was configured
        assert mock_logger.setLevel.called
        assert mock_logger.addHandler.called
        assert mock_logger.propagate == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])