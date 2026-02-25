# Veritix API Reference

> Base URL: `http://localhost:8000`  
> Auto-generated OpenAPI docs are also available at `/docs` (Swagger UI) and `/redoc`.

---

## Table of Contents

- [Health & Metrics](#health--metrics)
- [QR Code Endpoints](#qr-code-endpoints)
- [Analytics Endpoints](#analytics-endpoints)
- [ETL Trigger](#etl-trigger)
- [Scheduler](#scheduler)
- [Fraud Detection](#fraud-detection)
- [Scalper Prediction](#scalper-prediction)
- [Event Search & Recommendations](#event-search--recommendations)
- [Revenue Sharing](#revenue-sharing)
- [Daily Report](#daily-report)
- [Chat](#chat)

---

## Health & Metrics

### `GET /`

Returns a simple liveness message.

**Authentication:** None

**Response `200`**

```json
{
  "message": "Veritix Service is running. Check /health for status."
}
```

---

### `GET /health`

Full health check returning service name and API version.

**Authentication:** None

**Response `200`**

```json
{
  "status": "OK",
  "service": "Veritix Backend",
  "api_version": "0.1.0"
}
```

---

### `GET /metrics`

Exposes Prometheus-compatible metrics for scraping.

**Authentication:** None  
**Content-Type:** `text/plain; version=0.0.4`

**Response `200`** — Raw Prometheus exposition format text (counters, histograms, gauges for request counts, durations, QR generations/validations, fraud detections, ETL jobs, etc.)

---

## QR Code Endpoints

### `POST /generate-qr`

Generates a signed QR code image for a ticket.

**Authentication:** None (internal — ensure network-level protection in production)

**Request Body** (`application/json`)

| Field       | Type     | Required | Description              |
| ----------- | -------- | -------- | ------------------------ |
| `ticket_id` | `string` | Yes      | Unique ticket identifier |
| `event`     | `string` | Yes      | Event name or identifier |
| `user`      | `string` | Yes      | User identifier          |

```json
{
  "ticket_id": "TKT-001",
  "event": "Afrobeats Live 2025",
  "user": "user_abc123"
}
```

**Response `200`**

```json
{
  "qr_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

The `qr_base64` value is a Base64-encoded PNG image of the QR code.

**Error Responses**

| Status | Description                                                                        |
| ------ | ---------------------------------------------------------------------------------- |
| `500`  | `{"detail": "QR generation dependency missing"}` — `qrcode`/`pillow` not installed |

---

### `POST /validate-qr`

Validates a QR code by verifying its HMAC signature.

**Authentication:** None (public — used by venue scanners)

**Request Body** (`application/json`)

| Field     | Type     | Required | Description                              |
| --------- | -------- | -------- | ---------------------------------------- |
| `qr_text` | `string` | Yes      | Raw JSON string decoded from the QR code |

```json
{
  "qr_text": "{\"ticket_id\":\"TKT-001\",\"event\":\"Afrobeats Live 2025\",\"user\":\"user_abc123\",\"sig\":\"abc123def456\"}"
}
```

**Response `200` — Valid QR**

```json
{
  "isValid": true,
  "metadata": {
    "ticket_id": "TKT-001",
    "event": "Afrobeats Live 2025",
    "user": "user_abc123"
  }
}
```

**Response `200` — Invalid QR**

```json
{
  "isValid": false,
  "metadata": null
}
```

---

### `POST /qr/generate`

Router-level QR generation endpoint. Requires a service API key.

**Authentication:** `X-Service-Key` header (service key auth)  
**Rate Limit:** 60 requests/minute

**Response `200`**

```json
{
  "success": true,
  "msg": "QR generated successfully"
}
```

**Error Responses**

| Status        | Description                                                             |
| ------------- | ----------------------------------------------------------------------- |
| `401` / `403` | Missing or invalid service key                                          |
| `429`         | `{"success": false, "error": "Rate limit exceeded. Try again in 60s."}` |

---

### `POST /qr/verify`

Router-level public QR verification endpoint.

**Authentication:** None  
**Rate Limit:** 30 requests/minute

**Response `200`**

```json
{
  "success": true,
  "msg": "QR verified successfully"
}
```

**Error Responses**

| Status | Description                                                             |
| ------ | ----------------------------------------------------------------------- |
| `429`  | `{"success": false, "error": "Rate limit exceeded. Try again in 60s."}` |

---

## Analytics Endpoints

### `GET /stats`

Returns aggregated ticket scan, transfer, and invalid attempt statistics. Returns stats for all events if no `event_id` is provided.

**Authentication:** None

**Query Parameters**

| Param      | Type     | Required | Description                      |
| ---------- | -------- | -------- | -------------------------------- |
| `event_id` | `string` | No       | Filter stats to a specific event |

**Response `200` — Single event**

```json
{
  "event_id": "evt_001",
  "scan_count": 320,
  "transfer_count": 45,
  "invalid_attempt_count": 7
}
```

**Response `200` — All events**

```json
[
  {
    "event_id": "evt_001",
    "scan_count": 320,
    "transfer_count": 45,
    "invalid_attempt_count": 7
  },
  {
    "event_id": "evt_002",
    "scan_count": 190,
    "transfer_count": 12,
    "invalid_attempt_count": 2
  }
]
```

**Error Responses**

| Status | Description                                                  |
| ------ | ------------------------------------------------------------ |
| `500`  | `{"detail": "Failed to retrieve analytics stats: <reason>"}` |

---

### `GET /stats/scans`

Returns recent ticket scan records for an event.

**Authentication:** None

**Query Parameters**

| Param      | Type      | Required | Default | Description                     |
| ---------- | --------- | -------- | ------- | ------------------------------- |
| `event_id` | `string`  | Yes      | —       | Event identifier                |
| `limit`    | `integer` | No       | `50`    | Max number of records to return |

**Response `200`**

```json
{
  "event_id": "evt_001",
  "scans": [
    {
      "ticket_id": "TKT-001",
      "scanned_at": "2025-06-01T14:32:10Z",
      "is_valid": true
    }
  ],
  "count": 1
}
```

**Error Responses**

| Status | Description                                               |
| ------ | --------------------------------------------------------- |
| `500`  | `{"detail": "Failed to retrieve recent scans: <reason>"}` |

---

### `GET /stats/transfers`

Returns recent ticket transfer records for an event.

**Authentication:** None

**Query Parameters**

| Param      | Type      | Required | Default | Description                     |
| ---------- | --------- | -------- | ------- | ------------------------------- |
| `event_id` | `string`  | Yes      | —       | Event identifier                |
| `limit`    | `integer` | No       | `50`    | Max number of records to return |

**Response `200`**

```json
{
  "event_id": "evt_001",
  "transfers": [
    {
      "ticket_id": "TKT-002",
      "from_user": "user_abc",
      "to_user": "user_xyz",
      "transferred_at": "2025-06-01T10:00:00Z"
    }
  ],
  "count": 1
}
```

**Error Responses**

| Status | Description                                                   |
| ------ | ------------------------------------------------------------- |
| `500`  | `{"detail": "Failed to retrieve recent transfers: <reason>"}` |

---

### `GET /stats/invalid-attempts`

Returns recent invalid scan attempt records for an event.

**Authentication:** None

**Query Parameters**

| Param      | Type      | Required | Default | Description                     |
| ---------- | --------- | -------- | ------- | ------------------------------- |
| `event_id` | `string`  | Yes      | —       | Event identifier                |
| `limit`    | `integer` | No       | `50`    | Max number of records to return |

**Response `200`**

```json
{
  "event_id": "evt_001",
  "attempts": [
    {
      "ticket_id": "TKT-FAKE",
      "attempted_at": "2025-06-01T15:00:00Z",
      "reason": "invalid_signature"
    }
  ],
  "count": 1
}
```

**Error Responses**

| Status | Description                                                   |
| ------ | ------------------------------------------------------------- |
| `500`  | `{"detail": "Failed to retrieve invalid attempts: <reason>"}` |

---

### `GET /analytics/summary`

Returns a platform-wide aggregated summary of all events and sales. Result is cached for 60 seconds.

**Authentication:** Bearer token (`Authorization: Bearer <token>`)

**Response `200`**

```json
{
  "total_events": 12,
  "total_tickets_sold": 4800,
  "total_revenue_xlm": "96000.00",
  "total_revenue_usd": "48000.00",
  "last_etl_at": "2025-06-01T08:00:00Z",
  "generated_at": "2025-06-01T14:55:22.341Z"
}
```

**Error Responses**

| Status | Description                     |
| ------ | ------------------------------- |
| `401`  | Missing or invalid bearer token |

---

## ETL Trigger

The ETL pipeline runs automatically on the configured schedule. There is no dedicated HTTP trigger endpoint — the scheduler calls `run_etl_once()` directly. See [ETL Pipeline docs](./etl-pipeline.md) for full details and manual invocation.

---

## Scheduler

The background ETL scheduler is configured at application startup via environment variables. See [ETL Pipeline — Scheduler Configuration](./etl-pipeline.md#scheduler-configuration) for options.

---

## Fraud Detection

### `POST /check-fraud`

Evaluates a set of ticket events against fraud detection rules and returns any triggered rule names.

**Authentication:** None

**Request Body** (`application/json`)

| Field    | Type            | Required | Description                              |
| -------- | --------------- | -------- | ---------------------------------------- |
| `events` | `array[object]` | Yes      | List of ticket event objects to evaluate |

```json
{
  "events": [
    {
      "ticket_id": "TKT-099",
      "user_id": "user_suspicious",
      "tickets_per_txn": 10,
      "txns_per_min": 8.5,
      "avg_price_ratio": 1.9,
      "account_age_days": 1,
      "zip_mismatch": 1,
      "device_changes": 5
    }
  ]
}
```

**Response `200`**

```json
{
  "triggered_rules": ["high_volume_purchase", "new_account_bulk_buy"]
}
```

If no rules are triggered, `triggered_rules` will be an empty array `[]`.

---

## Scalper Prediction

### `POST /predict-scalper`

Runs a trained logistic regression model to estimate the probability that a transaction is from a scalper.

**Authentication:** None

**Request Body** (`application/json`)

| Field      | Type            | Required | Description                                                                                                                  |
| ---------- | --------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `features` | `array[number]` | Yes      | 6-element feature vector: `[tickets_per_txn, txns_per_min, avg_price_ratio, account_age_days, zip_mismatch, device_changes]` |

```json
{
  "features": [8, 6.5, 1.8, 10, 1, 4]
}
```

**Response `200`**

```json
{
  "probability": 0.9231
}
```

`probability` is a float in the range `[0.0, 1.0]`. Values closer to `1.0` indicate higher likelihood of scalping.

**Error Responses**

| Status | Description                                                                                         |
| ------ | --------------------------------------------------------------------------------------------------- |
| `503`  | `{"detail": "Model not ready"}` — model has not been trained yet (e.g., `SKIP_MODEL_TRAINING=true`) |

---

## Event Search & Recommendations

### `POST /search-events`

Searches for events using natural language keyword extraction.

**Authentication:** None

**Request Body** (`application/json`)

| Field   | Type     | Required | Description                   |
| ------- | -------- | -------- | ----------------------------- |
| `query` | `string` | Yes      | Natural language search query |

```json
{
  "query": "music events in Lagos this weekend"
}
```

**Response `200`**

```json
{
  "query": "music events in Lagos this weekend",
  "results": [
    {
      "id": "evt_afrobeats_01",
      "name": "Afrobeats Live Lagos",
      "description": "A night of Afrobeats music",
      "event_type": "music",
      "location": "Lagos, Nigeria",
      "date": "2025-06-07",
      "price": 5000.0,
      "capacity": 2000
    }
  ],
  "count": 1,
  "keywords_extracted": ["music", "lagos", "weekend"]
}
```

**Error Responses**

| Status | Description                             |
| ------ | --------------------------------------- |
| `500`  | `{"detail": "Search failed: <reason>"}` |

---

### `POST /recommend-events`

Returns up to 3 collaborative-filter-based event recommendations for a user.

**Authentication:** None

**Request Body** (`application/json`)

| Field     | Type     | Required | Description                              |
| --------- | -------- | -------- | ---------------------------------------- |
| `user_id` | `string` | Yes      | The user to generate recommendations for |

```json
{
  "user_id": "user1"
}
```

**Response `200`**

```json
{
  "recommendations": ["concert_C", "concert_D", "concert_E"]
}
```

**Error Responses**

| Status | Description                                 |
| ------ | ------------------------------------------- |
| `404`  | `{"detail": {"message": "User not found"}}` |

---

## Revenue Sharing

### `POST /calculate-revenue-share`

Calculates revenue distributions for all stakeholders for a single event.

**Authentication:** None

**Request Body** (`application/json`)

| Field             | Type      | Required | Description                        |
| ----------------- | --------- | -------- | ---------------------------------- |
| `event_id`        | `string`  | Yes      | Unique event identifier            |
| `total_sales`     | `number`  | Yes      | Gross ticket sales amount          |
| `ticket_count`    | `integer` | Yes      | Number of tickets sold             |
| `currency`        | `string`  | No       | Currency code, defaults to `"USD"` |
| `additional_fees` | `object`  | No       | Map of fee name to amount          |

```json
{
  "event_id": "event_123",
  "total_sales": 10000.0,
  "ticket_count": 100,
  "currency": "USD",
  "additional_fees": {
    "service_fee": 50.0
  }
}
```

**Response `200`**

```json
{
  "event_id": "event_123",
  "total_paid_out": 10000.0,
  "distributions": [
    { "stakeholder": "organizer", "amount": 8500.0, "percentage": 85.0 },
    { "stakeholder": "platform", "amount": 1000.0, "percentage": 10.0 },
    { "stakeholder": "charity", "amount": 500.0, "percentage": 5.0 }
  ]
}
```

**Error Responses**

| Status | Description                                                |
| ------ | ---------------------------------------------------------- |
| `400`  | `{"detail": {"errors": ["total_sales must be positive"]}}` |
| `500`  | `{"detail": "Revenue calculation failed: <reason>"}`       |

---

### `POST /calculate-revenue-share/batch`

Calculates revenue distributions for multiple events in one request. Events that fail validation are silently skipped.

**Authentication:** None

**Request Body** (`application/json`) — Array of `EventRevenueInput` objects (same schema as above)

```json
[
  {
    "event_id": "event_001",
    "total_sales": 5000.0,
    "ticket_count": 50,
    "currency": "USD"
  },
  {
    "event_id": "event_002",
    "total_sales": 12000.0,
    "ticket_count": 120,
    "currency": "USD"
  }
]
```

**Response `200`** — Array of `RevenueCalculationResult` objects (same shape as single endpoint)

---

### `GET /revenue-share/config`

Returns the current revenue sharing split configuration.

**Authentication:** None

**Response `200`**

```json
{
  "organizer_percentage": 85.0,
  "platform_percentage": 10.0,
  "charity_percentage": 5.0
}
```

---

### `GET /revenue-share/example`

Returns a pre-populated example `EventRevenueInput` payload for reference.

**Authentication:** None

**Response `200`**

```json
{
  "event_id": "event_123",
  "total_sales": 10000.0,
  "ticket_count": 100,
  "currency": "USD",
  "additional_fees": {
    "service_fee": 50.0
  }
}
```

---

## Daily Report

### `POST /generate-daily-report`

Generates a daily sales report in CSV or JSON format and returns a summary.

**Authentication:** None

**Request Body** (`application/json`)

| Field           | Type            | Required | Default | Description                      |
| --------------- | --------------- | -------- | ------- | -------------------------------- |
| `target_date`   | `string (date)` | No       | Today   | Date to report on (`YYYY-MM-DD`) |
| `output_format` | `string`        | No       | `"csv"` | `"csv"` or `"json"`              |

```json
{
  "target_date": "2025-06-01",
  "output_format": "csv"
}
```

**Response `200`**

```json
{
  "success": true,
  "report_path": "/tmp/reports/daily_report_2025-06-01.csv",
  "report_date": "2025-06-01",
  "summary": {
    "total_sales": 320,
    "total_revenue": 1600000.0,
    "total_transfers": 45,
    "invalid_scans": 7
  },
  "message": "Report generated successfully at /tmp/reports/daily_report_2025-06-01.csv"
}
```

**Error Responses**

| Status | Description                                        |
| ------ | -------------------------------------------------- |
| `500`  | `{"detail": "Report generation failed: <reason>"}` |

---

## Chat

### `WebSocket /ws/chat/{conversation_id}/{user_id}`

Real-time WebSocket chat endpoint. Connect and send JSON messages.

**Authentication:** None (ensure application-level auth before opening socket in production)

**Path Parameters**

| Param             | Description                            |
| ----------------- | -------------------------------------- |
| `conversation_id` | Unique conversation identifier         |
| `user_id`         | User participating in the conversation |

**Client → Server message format**

```json
{
  "content": "Hello, I need help with my ticket.",
  "sender_type": "user",
  "metadata": {}
}
```

**Server → Client broadcast** — the server broadcasts `ChatMessage` objects to all participants in the conversation.

---

### `POST /chat/{conversation_id}/messages`

Send a chat message via HTTP (non-WebSocket).

**Authentication:** None

**Path Parameters**

| Param             | Description         |
| ----------------- | ------------------- |
| `conversation_id` | Target conversation |

**Request Body** (`application/json`)

| Field         | Type     | Required | Description                  |
| ------------- | -------- | -------- | ---------------------------- |
| `sender_id`   | `string` | Yes      | ID of the sender             |
| `sender_type` | `string` | Yes      | `"user"` or `"agent"`        |
| `content`     | `string` | Yes      | Message body                 |
| `metadata`    | `object` | No       | Arbitrary key-value metadata |

```json
{
  "sender_id": "user_abc123",
  "sender_type": "user",
  "content": "I can't find my ticket PDF.",
  "metadata": {}
}
```

**Response `200`**

```json
{
  "status": "success",
  "message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**Error Responses**

| Status | Description                            |
| ------ | -------------------------------------- |
| `500`  | `{"detail": "Failed to send message"}` |

---

### `GET /chat/{conversation_id}/history`

Retrieve message history for a conversation.

**Authentication:** None

**Path Parameters**

| Param             | Description         |
| ----------------- | ------------------- |
| `conversation_id` | Target conversation |

**Query Parameters**

| Param   | Type      | Required | Default | Description            |
| ------- | --------- | -------- | ------- | ---------------------- |
| `limit` | `integer` | No       | `50`    | Max messages to return |

**Response `200`**

```json
{
  "conversation_id": "conv_001",
  "messages": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "sender_id": "user_abc123",
      "sender_type": "user",
      "content": "I can't find my ticket PDF.",
      "timestamp": "2025-06-01T14:00:00",
      "conversation_id": "conv_001",
      "metadata": {}
    }
  ],
  "count": 1
}
```

---

### `POST /chat/{conversation_id}/escalate`

Escalate a conversation to human support.

**Authentication:** None

**Request Body** (`application/json`)

| Field      | Type     | Required | Description                             |
| ---------- | -------- | -------- | --------------------------------------- |
| `reason`   | `string` | Yes      | Why the conversation is being escalated |
| `metadata` | `object` | No       | Additional context                      |

```json
{
  "reason": "User is requesting a refund beyond bot capabilities.",
  "metadata": { "priority": "high" }
}
```

**Response `200`**

```json
{
  "status": "success",
  "escalation_id": "esc_abc123",
  "reason": "User is requesting a refund beyond bot capabilities.",
  "timestamp": "2025-06-01T14:05:00.000000"
}
```

---

### `GET /chat/{conversation_id}/escalations`

List all escalation events for a conversation.

**Authentication:** None

**Response `200`**

```json
{
  "conversation_id": "conv_001",
  "escalations": [
    {
      "id": "esc_abc123",
      "reason": "User is requesting a refund beyond bot capabilities.",
      "timestamp": "2025-06-01T14:05:00"
    }
  ],
  "count": 1
}
```

---

### `GET /chat/user/{user_id}/conversations`

Get all conversation IDs a user is part of.

**Authentication:** None

**Path Parameters**

| Param     | Description     |
| --------- | --------------- |
| `user_id` | User identifier |

**Response `200`**

```json
{
  "user_id": "user_abc123",
  "conversations": ["conv_001", "conv_002"],
  "count": 2
}
```

---

## Error Codes Reference

| Status | Meaning                                                     |
| ------ | ----------------------------------------------------------- |
| `400`  | Bad request — validation error in request body              |
| `401`  | Unauthorized — missing or invalid authentication            |
| `403`  | Forbidden — insufficient permissions                        |
| `404`  | Not found — resource does not exist                         |
| `429`  | Too Many Requests — rate limit exceeded                     |
| `500`  | Internal Server Error — unexpected failure                  |
| `503`  | Service Unavailable — dependency not ready (e.g., ML model) |
