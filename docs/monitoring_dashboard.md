# Veritix Service Monitoring Dashboard

This document provides instructions for setting up monitoring dashboards using the Prometheus metrics exposed by the Veritix service.

## Available Metrics

### HTTP Request Metrics
- `http_requests_total` - Counter for total HTTP requests by method, endpoint, and status code
- `http_request_duration_seconds` - Histogram for HTTP request duration by method and endpoint
- `http_requests_in_progress` - Gauge for currently processing HTTP requests

### WebSocket Metrics
- `websocket_connections_total` - Gauge for active WebSocket connections

### Chat Metrics
- `chat_messages_total` - Counter for total chat messages by sender type and conversation
- `chat_conversations_active` - Gauge for active chat conversations

### Business Metrics
- `etl_jobs_total` - Counter for ETL jobs by status (success/failure)
- `ticket_scans_total` - Counter for ticket scans by result
- `fraud_detections_total` - Counter for fraud detection checks by rules triggered
- `qr_generations_total` - Counter for QR codes generated
- `qr_validations_total` - Counter for QR codes validated by result

## Grafana Dashboard Configuration

### 1. Import Dashboard

Create a new dashboard in Grafana and import the following JSON configuration:

```json
{
  "dashboard": {
    "id": null,
    "title": "Veritix Service Monitoring",
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "30s",
    "panels": [
      {
        "type": "graph",
        "title": "HTTP Request Rate",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}} {{status_code}}"
          }
        ],
        "yaxes": [
          {"format": "reqps", "label": "Requests per second"}
        ]
      },
      {
        "type": "graph",
        "title": "HTTP Request Duration (95th percentile)",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Duration (seconds)"}
        ]
      },
      {
        "type": "stat",
        "title": "Active WebSocket Connections",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "websocket_connections_total"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "none"
          }
        }
      },
      {
        "type": "stat",
        "title": "Active Chat Conversations",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 8},
        "targets": [
          {
            "expr": "chat_conversations_active"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "none"
          }
        }
      },
      {
        "type": "graph",
        "title": "Chat Message Volume",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "rate(chat_messages_total[5m])",
            "legendFormat": "{{sender_type}} ({{conversation_id}})"
          }
        ],
        "yaxes": [
          {"format": "short", "label": "Messages per second"}
        ]
      },
      {
        "type": "graph",
        "title": "ETL Job Status",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 12},
        "targets": [
          {
            "expr": "rate(etl_jobs_total[5m])",
            "legendFormat": "{{status}}"
          }
        ],
        "yaxes": [
          {"format": "short", "label": "Jobs per second"}
        ]
      },
      {
        "type": "graph",
        "title": "QR Operations",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 16},
        "targets": [
          {
            "expr": "rate(qr_generations_total[5m])",
            "legendFormat": "Generations"
          },
          {
            "expr": "rate(qr_validations_total[5m])",
            "legendFormat": "Validations ({{result}})"
          }
        ],
        "yaxes": [
          {"format": "short", "label": "Operations per second"}
        ]
      }
    ]
  }
}
```

### 2. Dashboard Variables

Add these variables to make the dashboard more interactive:

- **Endpoint**: `label_values(http_requests_total, endpoint)`
- **Method**: `label_values(http_requests_total, method)`
- **Status Code**: `label_values(http_requests_total, status_code)`

### 3. Alert Rules

Configure these alert rules in Grafana:

```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High error rate detected"
    description: "Error rate above 5% for 5 minutes"

# High latency
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High request latency"
    description: "95th percentile latency above 2 seconds"

# Low WebSocket connections
- alert: LowWebSocketConnections
  expr: websocket_connections_total < 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "No WebSocket connections"
    description: "No active WebSocket connections for 5 minutes"
```

## Prometheus Configuration

### 1. Add Target to Prometheus

Add the Veritix service to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'veritix'
    static_configs:
      - targets: ['localhost:8000']  # Adjust to your service address
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 2. Environment Variables

Configure logging and metrics through environment variables:

```bash
# Logging level
export LOG_LEVEL=INFO

# Enable ETL scheduler (for ETL metrics)
export ENABLE_ETL_SCHEDULER=true
export ETL_CRON="0 2 * * *"  # Run daily at 2 AM UTC
```

## Testing Metrics

### 1. Local Testing

Test the metrics endpoint locally:

```bash
# Start the service
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Check metrics endpoint
curl http://localhost:8000/metrics
```

### 2. Generate Test Load

Use tools like `ab` or `wrk` to generate load and observe metrics:

```bash
# Generate HTTP load
ab -n 1000 -c 10 http://localhost:8000/health

# Test chat functionality
# Open multiple browser tabs to /static/chat-widget.html
```

## Docker Compose Setup

For local development with monitoring stack:

```yaml
version: '3.8'
services:
  veritix:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - ENABLE_ETL_SCHEDULER=true
    depends_on:
      - postgres

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: veritix
      POSTGRES_USER: veritix
      POSTGRES_PASSWORD: veritix
    ports:
      - "5432:5432"

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
```

## Best Practices

1. **Log Levels**: Use appropriate log levels:
   - DEBUG: Detailed diagnostic information
   - INFO: General operational information
   - WARNING: Warning conditions
   - ERROR: Error conditions

2. **Metric Cardinality**: Be careful with high-cardinality labels that can impact performance

3. **Alerting**: Set appropriate thresholds based on your service's normal operating parameters

4. **Retention**: Configure appropriate retention periods for logs and metrics based on your requirements

5. **Security**: Protect the `/metrics` endpoint in production environments with appropriate authentication/authorization