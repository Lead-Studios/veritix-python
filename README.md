## Veritix Python Service

---

## Local Development

### Prerequisites

- Python 3.11+
- [Docker & Docker Compose](https://docs.docker.com/get-docker/) (for container targets)
- [Alembic](https://alembic.sqlalchemy.org/) (installed via `requirements.txt`)

### Quick start

```bash
git clone <repo-url>
cd veritix-python
make dev-setup       # copies .env.example → .env, creates .venv, installs deps
source .venv/bin/activate
make run             # starts the API at http://localhost:8000
```

`make dev-setup` is **idempotent** — running it a second time will not overwrite
your `.env` or recreate the virtualenv if they already exist.

---

### All make targets

| Target             | What it does                                                                                        |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| `make dev-setup`   | Copy `.env.example` → `.env` (skipped if `.env` exists), create `.venv`, install `requirements.txt` |
| `make run`         | Start the app with `uvicorn src.main:app --reload`                                                  |
| `make format`      | Auto-format all code with **black** and **isort**                                                   |
| `make lint-check`  | Check formatting without modifying files — exits non-zero if changes are needed (used in CI)        |
| `make lint`        | Run black, isort, and flake8 checks                                                                 |
| `make test`        | Run pytest with coverage (requires ≥ 80 % overall)                                                  |
| `make test-docker` | Run tests inside Docker with a live Postgres container                                              |
| `make security`    | Run `safety` and `bandit` security scans                                                            |
| `make docker`      | Build the Docker image and smoke-test it                                                            |
| `make docker-up`   | `docker compose up -d` — start the full stack in the background                                     |
| `make docker-down` | `docker compose down` — stop and remove containers                                                  |
| `make migrate`     | Apply all pending database migrations (`alembic upgrade head`)                                      |
| `make validate`    | Run the full CI validation script (`scripts/validate-ci.sh`)                                        |
| `make clean`       | Remove `__pycache__`, `.pytest_cache`, coverage files, and local Docker images                      |

---

### Environment variables

Copy `.env.example` to `.env` (done automatically by `make dev-setup`) and fill in the values:

| Variable                  | Required | Description                                                                            |
| ------------------------- | -------- | -------------------------------------------------------------------------------------- |
| `QR_SIGNING_KEY`          | ✅       | Secret used to sign QR payloads. Minimum 32 characters.                                |
| `DATABASE_URL`            | ✅       | Postgres connection string, e.g. `postgresql://veritix:veritix@localhost:5432/veritix` |
| `NEST_API_BASE_URL`       | ✅       | Base URL of the NestJS API                                                             |
| `NEST_API_TOKEN`          |          | Optional bearer token for the NestJS API                                               |
| `SESSION_TIMEOUT_MINUTES` |          | WebSocket session timeout in minutes (default `30`)                                    |
| `ENABLE_ETL_SCHEDULER`    |          | Set `true` to run the ETL on a schedule                                                |
| `ETL_CRON`                |          | Cron expression (UTC) — takes precedence over `ETL_INTERVAL_MINUTES`                   |
| `ETL_INTERVAL_MINUTES`    |          | ETL polling interval in minutes (default `15`)                                         |
| `BQ_ENABLED`              |          | Set `true` to enable BigQuery loading                                                  |
| `BQ_PROJECT_ID`           |          | GCP project ID                                                                         |
| `BQ_DATASET`              |          | BigQuery dataset name                                                                  |
| `BQ_LOCATION`             |          | BigQuery dataset location (e.g. `US`)                                                  |

---

## Run with Docker

Prerequisites: Docker and Docker Compose installed.

```bash
# Build and start the stack (app + Postgres)
make docker-up

# Tail logs
docker compose logs -f

# Tear down
make docker-down
```

The API will be available at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/health
```

---

## ETL Pipeline

This service includes a simple ETL that pulls ticketing data from a NestJS API and loads summary tables into Postgres (and optionally BigQuery).

- Extracts `events` and `ticket-sales` from `NEST_API_BASE_URL`.
- Transforms into two summary tables:
  - `event_sales_summary` (event-level totals)
  - `daily_ticket_sales` (event/day breakdown)
- Loads into Postgres automatically if `DATABASE_URL` is set. BigQuery load is optional.

Tables are created automatically on first load.

---

## Running Tests

```bash
# Unit + integration tests with coverage
make test

# Tests against a live Postgres container
make test-docker
```

The CI pipeline enforces a minimum of 80 % code coverage.

---

## Database Migrations

```bash
# Apply all pending migrations
make migrate

# (Equivalent to)
alembic upgrade head
```

---

## Stop and Clean Up

```bash
make docker-down   # stop containers
make clean         # remove caches and build artefacts
```
