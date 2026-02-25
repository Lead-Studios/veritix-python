# ETL Pipeline

The Veritix ETL pipeline pulls raw ticketing data from an upstream NestJS API, aggregates it into summary tables, and loads the results into PostgreSQL and optionally Google BigQuery.

Source: `src/etl/`

---

## Pipeline Overview

```
NestJS API (/events, /ticket-sales)
        │
        ▼
    [ Extract ]          src/etl/extract.py
        │  paginated fetch with retry
        ▼
    [ Transform ]        src/etl/__init__.py → transform_summary()
        │  aggregate by event and by event+day
        ▼
    [ Load ]
        ├── PostgreSQL   load_postgres()
        └── BigQuery     load_bigquery()  (optional)
```

---

## Extract

**Source:** `src/etl/extract.py` — `extract_events_and_sales()`

### Data Sources

| Endpoint                               | Description                           |
| -------------------------------------- | ------------------------------------- |
| `GET {NEST_API_BASE_URL}/events`       | All event records, paginated          |
| `GET {NEST_API_BASE_URL}/ticket-sales` | All ticket sale records (single page) |

Authentication to the upstream API is done via `Authorization: Bearer {NEST_API_TOKEN}` if the token is set.

### Fields Extracted

**Events** — mapped to `EventRecord`

| Source Field       | Normalised As | Description                          |
| ------------------ | ------------- | ------------------------------------ |
| `id` or `event_id` | `event_id`    | Unique event identifier              |
| `name` or `title`  | `event_name`  | Human-readable event name            |
| _(all fields)_     | `raw`         | Full raw dict retained for transform |

**Ticket Sales** — mapped to `TicketSaleRecord`

| Source Field                              | Normalised As  | Description                               |
| ----------------------------------------- | -------------- | ----------------------------------------- |
| `event_id`, `eventId`, or `event`         | `event_id`     | Parent event reference                    |
| `quantity` or `qty`                       | `quantity`     | Number of tickets in the transaction      |
| `price`, `unit_price`, or `amount`        | `price`        | Per-ticket price                          |
| `total_amount`                            | `total_amount` | Computed as `quantity × price` if missing |
| `sale_date`, `created_at`, or `timestamp` | `sale_date`    | ISO 8601 date string                      |

### Retry & Pagination

- **Retries:** Up to 3 attempts per request with exponential back-off (1 s, 2 s) on 5xx errors or network timeouts.
- **Timeout:** 30 seconds per request.
- **Pagination:** The extractor inspects the response envelope for `pagination.next_page`, `pagination.nextPage`, `pagination.has_more`, top-level `next_page`, `nextPage`, or `has_more` fields and loops until no next page is signalled.

---

## Transform

**Source:** `src/etl/__init__.py` — `transform_summary(events, sales)`

The transform stage produces two sets of rows — no external I/O occurs here.

### `event_sales_summary` — Event-Level Totals

One row per `event_id`. Accumulates totals across all sales records for that event.

| Column          | Type        | Description                                |
| --------------- | ----------- | ------------------------------------------ |
| `event_id`      | `string`    | Primary key — unique event identifier      |
| `event_name`    | `string`    | Joined from the events list                |
| `total_tickets` | `integer`   | Sum of all `quantity` values               |
| `total_revenue` | `float`     | Sum of all `total_amount` values           |
| `last_updated`  | `timestamp` | UTC timestamp of when the ETL run executed |

### `daily_ticket_sales` — Event × Day Breakdown

One row per `(event_id, sale_date)` pair. Allows trending and day-level reporting.

| Column         | Type      | Description                                          |
| -------------- | --------- | ---------------------------------------------------- |
| `event_id`     | `string`  | Composite primary key (with `sale_date`)             |
| `sale_date`    | `date`    | Date of the sale; falls back to today if unparseable |
| `tickets_sold` | `integer` | Sum of tickets sold on this date for this event      |
| `revenue`      | `float`   | Sum of revenue on this date for this event           |

**Note:** If `sale_date` cannot be parsed from the source data, it defaults to the current UTC date.

---

## Load

### PostgreSQL — `load_postgres()`

**Trigger:** Runs whenever `DATABASE_URL` is set.

Tables are auto-created on first run via SQLAlchemy `metadata.create_all()`.

**Upsert rules (PostgreSQL `ON CONFLICT DO UPDATE`):**

| Table                 | Conflict Key            | Updated Columns                                                |
| --------------------- | ----------------------- | -------------------------------------------------------------- |
| `event_sales_summary` | `event_id`              | `event_name`, `total_tickets`, `total_revenue`, `last_updated` |
| `daily_ticket_sales`  | `(event_id, sale_date)` | `tickets_sold`, `revenue`                                      |

Running the pipeline multiple times is safe — all operations are idempotent upserts.

### BigQuery — `load_bigquery()` (Optional)

**Trigger:** Only runs when `BQ_ENABLED=true` AND `BQ_PROJECT_ID` is set AND the `google-cloud-bigquery` package is installed.

- Dataset is created automatically if it does not exist.
- Tables are created automatically if they do not exist.
- Rows are inserted via `insert_rows_json` (streaming insert — not idempotent by default; deduplicate upstream if needed).

**BigQuery Schema**

`event_sales_summary`

| Column          | BQ Type     |
| --------------- | ----------- |
| `event_id`      | `STRING`    |
| `event_name`    | `STRING`    |
| `total_tickets` | `INTEGER`   |
| `total_revenue` | `NUMERIC`   |
| `last_updated`  | `TIMESTAMP` |

`daily_ticket_sales`

| Column         | BQ Type   |
| -------------- | --------- |
| `event_id`     | `STRING`  |
| `sale_date`    | `DATE`    |
| `tickets_sold` | `INTEGER` |
| `revenue`      | `NUMERIC` |

---

## Scheduler Configuration

The ETL scheduler is powered by [APScheduler](https://apscheduler.readthedocs.io/) and is started at application startup if enabled.

| Environment Variable     | Type      | Default                 | Description                                                                      |
| ------------------------ | --------- | ----------------------- | -------------------------------------------------------------------------------- |
| `ENABLE_ETL_SCHEDULER`   | `bool`    | `false`                 | Set to `true` to enable the background scheduler                                 |
| `ETL_CRON`               | `string`  | `""`                    | Cron expression (e.g. `"0 * * * *"` for hourly). Takes precedence over interval. |
| `ETL_INTERVAL_MINUTES`   | `integer` | `15`                    | Fallback polling interval in minutes when `ETL_CRON` is not set                  |
| `NEST_API_BASE_URL`      | `string`  | —                       | **Required.** Base URL of the upstream NestJS API                                |
| `NEST_API_TOKEN`         | `string`  | `""`                    | Bearer token for the upstream API (optional)                                     |
| `DATABASE_URL`           | `string`  | `""`                    | PostgreSQL connection string (e.g. `postgresql://user:pass@host/db`)             |
| `BQ_ENABLED`             | `bool`    | `false`                 | Enable BigQuery load                                                             |
| `BQ_PROJECT_ID`          | `string`  | `""`                    | GCP project ID                                                                   |
| `BQ_DATASET`             | `string`  | `"veritix"`             | BigQuery dataset name                                                            |
| `BQ_LOCATION`            | `string`  | `"US"`                  | BigQuery dataset location                                                        |
| `BQ_TABLE_EVENT_SUMMARY` | `string`  | `"event_sales_summary"` | BigQuery table name for event totals                                             |
| `BQ_TABLE_DAILY_SALES`   | `string`  | `"daily_ticket_sales"`  | BigQuery table name for daily breakdown                                          |

### Example `.env` for scheduled hourly ETL

```dotenv
ENABLE_ETL_SCHEDULER=true
ETL_CRON=0 * * * *
NEST_API_BASE_URL=https://api.internal.veritix.io
NEST_API_TOKEN=super_secret_token
DATABASE_URL=postgresql://veritix:password@postgres:5432/veritix
```

### Manual Trigger

To run the ETL pipeline once without the scheduler (e.g. for a backfill):

```python
from src.etl import run_etl_once
run_etl_once()
```

Or from a shell inside the running container:

```bash
docker compose exec app python -c "from src.etl import run_etl_once; run_etl_once()"
```

---

## Observability

The ETL pipeline emits structured logs at each stage (`log_info`, `log_error`) and increments the `ETL_JOBS_TOTAL` Prometheus counter, which is exposed at `GET /metrics`.

Key log events:

| Event                   | Fields                                                 |
| ----------------------- | ------------------------------------------------------ |
| `ETL job started`       | —                                                      |
| `ETL extract attempt`   | `dataset`, `attempt`, `status_code`, `record_count`    |
| `ETL extract completed` | `events_count`, `sales_count`                          |
| `ETL load completed`    | `database`, `event_summary_count`, `daily_sales_count` |
| `ETL job completed`     | —                                                      |
| `Postgres load failed`  | `error`                                                |
| `BigQuery load failed`  | `error`                                                |
