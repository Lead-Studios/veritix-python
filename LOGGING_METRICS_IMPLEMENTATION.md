# Structured Logging and Prometheus Metrics Implementation

## Overview

This implementation adds structured JSON logging and Prometheus metrics to the Veritix Python service. The solution provides:

1. **Structured JSON Logging** - Consistent, parseable log format with request IDs and metadata
2. **Prometheus Metrics** - Comprehensive service metrics for monitoring and alerting
3. **Request Tracking** - Automatic request ID generation and propagation
4. **Dashboard Integration** - Ready-to-use Grafana dashboard configurations

## Features Implemented

### Structured Logging
- JSON-formatted logs with consistent structure
- Automatic request ID generation and tracking
- Context-aware logging with metadata
- Configurable log levels
- Request/response logging with timing information

### Prometheus Metrics
- HTTP request metrics (count, duration, in-progress)
- WebSocket connection metrics
- Chat message metrics
- Business operation metrics (ETL, QR codes, fraud detection)
- Custom application metrics

### Middleware Components
- **RequestIDMiddleware** - Generates and tracks request IDs
- **MetricsMiddleware** - Collects and exposes Prometheus metrics
- Automatic correlation of logs and metrics

## File Changes

### New Files Created
1. `src/logging_config.py` - Core logging and metrics implementation
2. `docs/monitoring_dashboard.md` - Dashboard configuration and setup instructions
3. `tests/test_logging_metrics.py` - Comprehensive test suite

### Modified Files
1. `src/main.py` - Added logging/metrics middleware and updated endpoints
2. `src/websocket.py` - Updated to use structured logging
3. `src/manager.py` - Updated to use structured logging
4. `src/chat.py` - Updated to use structured logging and metrics
5. `src/etl.py` - Added logging and metrics to ETL operations
6. `requirements.txt` - Added `prometheus-client` dependency

## Configuration

### Environment Variables
```bash
# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Request ID header name (optional)
REQUEST_ID_HEADER=X-Request-ID
```

### Log Format
All logs are formatted as JSON with the following structure:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "veritix",
  "message": "User connected to chat",
  "request_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
  "module": "chat",
  "function": "connect",
  "line": 45,
  "extra_data": {
    "conversation_id": "conv_123",
    "user_id": "user_456",
    "total_connections": 2
  }
}
```

## Available Metrics

### HTTP Metrics
- `http_requests_total` - Counter for HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Histogram for request durations
- `http_requests_in_progress` - Gauge for active requests

### WebSocket Metrics
- `websocket_connections_total` - Gauge for active WebSocket connections

### Chat Metrics
- `chat_messages_total` - Counter for chat messages by sender type
- `chat_conversations_active` - Gauge for active conversations

### Business Metrics
- `etl_jobs_total` - Counter for ETL jobs by status
- `ticket_scans_total` - Counter for ticket scans by result
- `fraud_detections_total` - Counter for fraud checks by rules triggered
- `qr_generations_total` - Counter for QR code generations
- `qr_validations_total` - Counter for QR validations by result

## Usage Examples

### Basic Logging
```python
from src.logging_config import log_info, log_error, log_warning

# Simple info log
log_info("User action completed")

# Log with metadata
log_info("Database operation", {"table": "users", "operation": "insert"})

# Error logging
log_error("Database connection failed", {"error": "Connection timeout"})
```

### Custom Metrics
```python
from src.logging_config import CHAT_MESSAGES_TOTAL

# Increment chat message counter
CHAT_MESSAGES_TOTAL.labels(sender_type="user", conversation_id="conv123").inc()
```

### Accessing Request ID
```python
from src.logging_config import request_id_context

# Get current request ID
request_id = request_id_context.get()
```

## Testing

Run the logging and metrics tests:
```bash
# Run all tests
pytest tests/test_logging_metrics.py -v

# Run with coverage
pytest tests/test_logging_metrics.py --cov=src --cov-report=html
```

## Monitoring Setup

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'veritix'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard
Import the JSON configuration from `docs/monitoring_dashboard.md` or use the provided examples.

### Alert Rules
Example alert rules for critical service health:
- High error rate (>5% 5xx errors)
- High latency (>2 seconds 95th percentile)
- No WebSocket connections
- Failed ETL jobs

## Performance Considerations

1. **Log Volume**: JSON logs are more verbose than traditional logs
2. **Metric Cardinality**: Avoid high-cardinality labels in metrics
3. **Memory Usage**: Prometheus metrics are kept in memory
4. **Request Overhead**: Minimal overhead from middleware components

## Security Considerations

1. **Log Sanitization**: Avoid logging sensitive information
2. **Metrics Exposure**: Protect `/metrics` endpoint in production
3. **Request ID Generation**: Use cryptographically secure random IDs
4. **Log Retention**: Implement appropriate log retention policies

## Integration with Existing Systems

### Docker Compose
The logging works seamlessly with Docker container orchestration:
```yaml
version: '3.8'
services:
  veritix:
    # ... existing config
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Kubernetes
The JSON format is compatible with Fluentd/Elasticsearch/FluentBit:
```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    fluentd.log/format: "json"
```

## Migration Notes

When migrating from existing logging:

1. **Existing logs**: The old `logger.info()` calls continue to work
2. **Backward compatibility**: Standard Python logging remains functional
3. **Gradual migration**: Convert existing logging calls gradually
4. **Monitoring**: Existing metrics/dashboarding may need updates

## Troubleshooting

### Common Issues
1. **Missing metrics**: Verify `/metrics` endpoint is accessible
2. **JSON parsing errors**: Check for non-serializable objects in extra_data
3. **High memory usage**: Review metric cardinality and retention settings
4. **Performance impact**: Monitor response times with high logging volumes

### Debugging Tips
1. Set `LOG_LEVEL=DEBUG` for verbose output
2. Check `/metrics` endpoint for proper metric collection
3. Verify request ID propagation through microservices
4. Use Prometheus query language for real-time metrics debugging

## Next Steps

Consider implementing:

1. **Distributed tracing** (OpenTelemetry) for complex request flows
2. **Centralized logging** integration with ELK/EFK stack
3. **Advanced alerting** with machine learning-based anomaly detection
4. **Log aggregation** across multiple service instances
5. **Custom dashboards** for specific business metrics

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboard Guide](https://grafana.com/docs/grafana/latest/dashboards/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Structured Logging Concepts](https://www.honeycomb.io/blog/structured-logging)