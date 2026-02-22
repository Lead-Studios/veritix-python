"""Structured logging and Prometheus metrics for the Veritix service."""
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


# Context variable for request ID
request_id_context: ContextVar[str] = ContextVar('request_id', default='')


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Get request ID from context
        request_id = request_id_context.get()
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': request_id,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
            
        return json.dumps(log_entry, separators=(',', ':'))


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and track request IDs."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_context.set(request_id)
        
        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log request completion
        logger = logging.getLogger('veritix.request')
        logger.info(
            'Request completed',
            extra={
                'extra_data': {
                    'method': request.method,
                    'path': str(request.url.path),
                    'status_code': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'client_ip': self._get_client_ip(request),
                    'user_agent': request.headers.get('user-agent', 'unknown')
                }
            }
        )
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        # Fallback to client host
        return request.client.host if request.client else 'unknown'


# Prometheus Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint']
)

WEBSOCKET_CONNECTIONS = Gauge(
    'websocket_connections_total',
    'Number of active WebSocket connections'
)

CHAT_MESSAGES_TOTAL = Counter(
    'chat_messages_total',
    'Total chat messages sent',
    ['sender_type', 'conversation_id']
)

ETL_JOBS_TOTAL = Counter(
    'etl_jobs_total',
    'Total ETL jobs executed',
    ['status']
)

TICKET_SCANS_TOTAL = Counter(
    'ticket_scans_total',
    'Total ticket scans processed',
    ['result']
)

FRAUD_DETECTIONS_TOTAL = Counter(
    'fraud_detections_total',
    'Total fraud detection checks',
    ['rules_triggered']
)

QR_GENERATIONS_TOTAL = Counter(
    'qr_generations_total',
    'Total QR codes generated'
)

QR_VALIDATIONS_TOTAL = Counter(
    'qr_validations_total',
    'Total QR codes validated',
    ['result']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        endpoint = self._get_endpoint_name(request)
        
        # Increment in-progress gauge
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            # Decrement in-progress gauge
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
            duration = time.time() - start_time
            
            # Update metrics
            REQUEST_COUNT.labels(
                method=method, 
                endpoint=endpoint, 
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method, 
                endpoint=endpoint
            ).observe(duration)
        
        return response
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Get normalized endpoint name for metrics."""
        path = str(request.url.path)
        # Normalize dynamic paths
        if '/ws/chat/' in path:
            return '/ws/chat/{conversation_id}/{user_id}'
        elif '/chat/' in path and '/messages' in path:
            return '/chat/{conversation_id}/messages'
        elif '/chat/' in path and '/history' in path:
            return '/chat/{conversation_id}/history'
        elif '/chat/' in path and '/escalate' in path:
            return '/chat/{conversation_id}/escalate'
        elif path.startswith('/chat/user/'):
            return '/chat/user/{user_id}/conversations'
        return path


def setup_logging(level: str = 'INFO') -> None:
    """Set up structured JSON logging."""
    # Create logger
    logger = logging.getLogger('veritix')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Set up other module loggers
    for module in ['veritix.etl', 'veritix.chat', 'veritix.request', 
                   'veritix.report_service', 'ticket_scans.manager']:
        mod_logger = logging.getLogger(module)
        mod_logger.setLevel(getattr(logging, level.upper()))
        mod_logger.handlers.clear()
        mod_logger.addHandler(console_handler)
        mod_logger.propagate = False


def get_metrics() -> bytes:
    """Generate Prometheus metrics in proper format."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST


# Convenience functions for logging with extra data
def log_info(message: str, extra_data: Optional[Dict[str, Any]] = None, logger_name: str = 'veritix') -> None:
    """Log info message with structured data."""
    logger = logging.getLogger(logger_name)
    if extra_data:
        logger.info(message, extra={'extra_data': extra_data})
    else:
        logger.info(message)


def log_error(message: str, extra_data: Optional[Dict[str, Any]] = None, logger_name: str = 'veritix') -> None:
    """Log error message with structured data."""
    logger = logging.getLogger(logger_name)
    if extra_data:
        logger.error(message, extra={'extra_data': extra_data})
    else:
        logger.error(message)


def log_warning(message: str, extra_data: Optional[Dict[str, Any]] = None, logger_name: str = 'veritix') -> None:
    """Log warning message with structured data."""
    logger = logging.getLogger(logger_name)
    if extra_data:
        logger.warning(message, extra={'extra_data': extra_data})
    else:
        logger.warning(message)