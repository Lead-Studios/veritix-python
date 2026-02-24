## Veritix Python Service

### Run with Docker

Prerequisites: Docker and Docker Compose installed.

1) Build the image:
```bash
docker compose build
```

2) Start the stack (app + Postgres):
```bash
docker compose up -d
```

The API will be available at `http://localhost:8000`. The service runs with `uvicorn src.main:app --host 0.0.0.0 --port 8000`.

Health check:
```bash
curl http://localhost:8000/health
```

### Environment Variables

- `QR_SIGNING_KEY`: Secret used to sign and validate QR payloads. Required at startup with minimum length of 32 characters.

### ETL Pipeline

This service includes a simple ETL that pulls ticketing data from a NestJS API and loads summary tables into Postgres (and optionally BigQuery).

- Extracts `events` and `ticket-sales` from `NEST_API_BASE_URL`.
- Transforms into two summary tables:
  - `event_sales_summary` (event-level totals)
  - `daily_ticket_sales` (event/day breakdown)
- Loads into Postgres automatically if `DATABASE_URL` is set. BigQuery load is optional.

#### Configure

Copy `.env.example` to `.env` and set:

- `DATABASE_URL`: Postgres connection string.
- `NEST_API_BASE_URL`: Base URL of the NestJS API (e.g., `https://nest.example.com/api`).
- `NEST_API_TOKEN`: Optional bearer token.
- `ENABLE_ETL_SCHEDULER`: Set to `true` to enable periodic ETL.
- `ETL_CRON`: Optional cron expression (UTC). If not set, uses `ETL_INTERVAL_MINUTES`.
- `ETL_INTERVAL_MINUTES`: Interval for ETL run (default 15).
- BigQuery (optional): `BQ_ENABLED`, `BQ_PROJECT_ID`, `BQ_DATASET`, `BQ_LOCATION`.

#### Run

- Docker: `docker compose up -d` will start app and Postgres. Set env vars in compose or `.env`.
- Local: `python run.py` starts the API; scheduler runs if enabled.

Tables are created automatically on first load.

### Stop and Clean Up
```bash
docker compose down
```

## Running tests

Install test dependencies (preferably inside a virtualenv):

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the test suite with coverage:

```powershell
python -m pytest --cov=src --cov-report=term-missing
```

The GitHub Actions workflow is configured to fail if overall coverage falls below 70%.

