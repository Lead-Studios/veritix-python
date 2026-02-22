# Analytics Module Documentation

## Overview

The Analytics Module tracks ticket scans, transfers, and invalid attempts, storing the data in PostgreSQL (with fallback to SQLite). It provides real-time analytics through the `/stats` endpoint and maintains detailed logs of all activities.

## Features

- **Ticket Scan Tracking**: Logs every ticket scan with validity status, location, and device information
- **Transfer Tracking**: Records all ticket transfers between users with success/failure status
- **Invalid Attempt Monitoring**: Tracks failed scans, unauthorized transfers, and other invalid activities
- **Real-time Statistics**: Provides instant access to event-specific analytics
- **Flexible Storage**: Works with both PostgreSQL and SQLite databases
- **Structured Logging**: All operations are logged with detailed metadata

## Database Schema

### Tables

#### `ticket_scans`
Stores information about each ticket scan:
- `id`: Primary key, auto-incrementing integer
- `ticket_id`: Identifier for the ticket (indexed)
- `event_id`: Identifier for the event (indexed)
- `scanner_id`: Identifier for the scanner device
- `scan_timestamp`: Timestamp of the scan (indexed)
- `is_valid`: Boolean indicating if the scan was valid
- `location`: Location where scan occurred
- `device_info`: Information about the scanning device
- `additional_metadata`: JSON string for flexible metadata

#### `ticket_transfers`
Tracks all ticket transfers between users:
- `id`: Primary key, auto-incrementing integer
- `ticket_id`: Identifier for the ticket (indexed)
- `event_id`: Identifier for the event (indexed)
- `from_user_id`: ID of the user transferring from
- `to_user_id`: ID of the user transferring to
- `transfer_timestamp`: Timestamp of the transfer (indexed)
- `transfer_reason`: Reason for the transfer
- `ip_address`: IP address of the transfer request
- `user_agent`: User agent string of the client
- `is_successful`: Boolean indicating if transfer succeeded
- `additional_metadata`: JSON string for flexible metadata

#### `invalid_attempts`
Records failed or invalid operations:
- `id`: Primary key, auto-incrementing integer
- `attempt_type`: Type of attempt ('scan', 'transfer', 'validation', etc.) (indexed)
- `ticket_id`: Identifier for the ticket (indexed)
- `event_id`: Identifier for the event (indexed)
- `attempt_timestamp`: Timestamp of the attempt (indexed)
- `reason`: Reason for the failure
- `ip_address`: IP address of the attempt
- `user_agent`: User agent string of the client
- `additional_metadata`: JSON string for flexible metadata

#### `analytics_stats`
Pre-calculated statistics for performance:
- `id`: Primary key, auto-incrementing integer
- `event_id`: Identifier for the event (indexed)
- `stat_date`: Date of the statistics (indexed)
- `scan_count`: Total number of scans
- `transfer_count`: Total number of transfers
- `invalid_attempt_count`: Total number of invalid attempts
- `valid_scan_count`: Count of valid scans
- `invalid_scan_count`: Count of invalid scans
- `successful_transfer_count`: Count of successful transfers
- `failed_transfer_count`: Count of failed transfers

## API Endpoints

### Get Event Statistics
```
GET /stats?event_id={event_id}
```
Returns detailed statistics for a specific event.

**Parameters:**
- `event_id` (optional): Specific event to get stats for. If omitted, returns stats for all events.

**Response:**
```json
{
  "event_id": "event_456",
  "scan_count": 150,
  "transfer_count": 25,
  "invalid_attempt_count": 5,
  "valid_scan_count": 145,
  "invalid_scan_count": 5,
  "successful_transfer_count": 23,
  "failed_transfer_count": 2,
  "last_updated": "2024-01-15T10:30:45.123456"
}
```

### Get All Events Statistics
```
GET /stats
```
Returns statistics for all events.

**Response:**
```json
{
  "event_456": {
    "event_id": "event_456",
    "scan_count": 150,
    "transfer_count": 25,
    "invalid_attempt_count": 5,
    "valid_scan_count": 145,
    "invalid_scan_count": 5,
    "successful_transfer_count": 23,
    "failed_transfer_count": 2,
    "last_updated": "2024-01-15T10:30:45.123456"
  },
  "event_789": {
    "event_id": "event_789",
    "scan_count": 85,
    "transfer_count": 12,
    "invalid_attempt_count": 3,
    "valid_scan_count": 82,
    "invalid_scan_count": 3,
    "successful_transfer_count": 11,
    "failed_transfer_count": 1,
    "last_updated": "2024-01-15T10:30:45.123456"
  }
}
```

### Get Recent Scans
```
GET /stats/scans?event_id={event_id}&limit={limit}
```
Returns recent scan records for an event.

**Parameters:**
- `event_id` (required): Event to get scans for
- `limit` (optional, default: 50): Maximum number of records to return

**Response:**
```json
{
  "event_id": "event_456",
  "scans": [
    {
      "id": 1,
      "ticket_id": "ticket_123",
      "scanner_id": "scanner_001",
      "scan_timestamp": "2024-01-15T10:30:45.123456",
      "is_valid": true,
      "location": "Main Gate"
    }
  ],
  "count": 1
}
```

### Get Recent Transfers
```
GET /stats/transfers?event_id={event_id}&limit={limit}
```
Returns recent transfer records for an event.

**Parameters:**
- `event_id` (required): Event to get transfers for
- `limit` (optional, default: 50): Maximum number of records to return

**Response:**
```json
{
  "event_id": "event_456",
  "transfers": [
    {
      "id": 1,
      "ticket_id": "ticket_123",
      "from_user_id": "user_abc",
      "to_user_id": "user_def",
      "transfer_timestamp": "2024-01-15T10:30:45.123456",
      "is_successful": true,
      "transfer_reason": "gift"
    }
  ],
  "count": 1
}
```

### Get Invalid Attempts
```
GET /stats/invalid-attempts?event_id={event_id}&limit={limit}
```
Returns recent invalid attempt records for an event.

**Parameters:**
- `event_id` (required): Event to get invalid attempts for
- `limit` (optional, default: 50): Maximum number of records to return

**Response:**
```json
{
  "event_id": "event_456",
  "attempts": [
    {
      "id": 1,
      "attempt_type": "scan",
      "ticket_id": "ticket_123",
      "attempt_timestamp": "2024-01-15T10:30:45.123456",
      "reason": "invalid_qr",
      "ip_address": "192.168.1.1"
    }
  ],
  "count": 1
}
```

## Service Functions

### Log Ticket Scan
```python
analytics_service.log_ticket_scan(
    ticket_id="ticket_123",
    event_id="event_456",
    scanner_id="scanner_789",
    is_valid=True,
    location="Main Entrance",
    device_info="iPhone iOS 15",
    additional_metadata={"battery_level": 80}
)
```

### Log Ticket Transfer
```python
analytics_service.log_ticket_transfer(
    ticket_id="ticket_123",
    event_id="event_456",
    from_user_id="user_abc",
    to_user_id="user_def",
    transfer_reason="gift",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    is_successful=True,
    additional_metadata={"platform": "mobile"}
)
```

### Log Invalid Attempt
```python
analytics_service.log_invalid_attempt(
    attempt_type="scan",
    reason="expired_ticket",
    ticket_id="ticket_123",
    event_id="event_456",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    additional_metadata={"error_code": "EXPIRED_001"}
)
```

## Database Configuration

By default, the service looks for a PostgreSQL database using the `DATABASE_URL` environment variable. If not found, it falls back to SQLite.

**Environment Variable:**
```
DATABASE_URL=postgresql://username:password@localhost:5432/veritix_analytics
```

## Performance Optimization

- All frequently queried columns are indexed
- Pre-calculated statistics stored in `analytics_stats` table
- Automatic cleanup of old records (configurable)
- Connection pooling managed by SQLAlchemy

## Data Retention

The system maintains historical data indefinitely. For production environments, implement a data archival process to manage storage costs.

## Error Handling

All API endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `500`: Internal server error

All errors are logged using the structured logging system.

## Testing

Run the analytics tests:
```bash
pytest tests/test_analytics.py -v
```

## Integration

The analytics module integrates with:
- **Structured Logging**: All operations are logged with request IDs and metadata
- **Prometheus Metrics**: Database operations are tracked as metrics
- **Revenue Sharing**: Transfer data can inform revenue calculations
- **Security**: Invalid attempts help detect fraudulent activities