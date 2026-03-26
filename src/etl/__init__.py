import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    Column,
    Date,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    TIMESTAMP,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

try:
    from google.cloud import bigquery  # type: ignore[import-untyped]
except Exception:
    bigquery = None  # Optional dependency

from src.logging_config import ETL_JOBS_TOTAL, log_error, log_info, log_warning
from src.config import get_settings
from .extract import extract_events_and_sales

logger = logging.getLogger("veritix.etl")


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def _safe_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Validation  (issue #162)
# ---------------------------------------------------------------------------

def validate_rows(
    event_summary_rows: List[Dict[str, Any]],
    daily_rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """Reject malformed rows before they reach the database.

    Rules:
    - event_summary row: ``event_id`` must be non-empty.
    - event_summary row: ``total_tickets`` and ``total_revenue`` must be >= 0.
    - daily row: ``event_id`` must be non-empty.
    - daily row: ``sale_date`` must not be more than 1 day in the future.

    Every rejected row is logged as a warning so it remains traceable.

    Returns:
        (valid_event_rows, valid_daily_rows, rejected_count)
    """
    rejected_count = 0
    valid_event_rows: List[Dict[str, Any]] = []
    today = datetime.now(tz=timezone.utc).date()

    for row in event_summary_rows:
        event_id = row.get("event_id")
        if not event_id:
            log_warning("ETL validate: rejected event row — empty event_id", {"row": row})
            rejected_count += 1
            continue
        if _safe_int(row.get("total_tickets", 0)) < 0:
            log_warning(
                "ETL validate: rejected event row — negative total_tickets",
                {"row": row},
            )
            rejected_count += 1
            continue
        if _safe_float(row.get("total_revenue", 0.0)) < 0:
            log_warning(
                "ETL validate: rejected event row — negative total_revenue",
                {"row": row},
            )
            rejected_count += 1
            continue
        valid_event_rows.append(row)

    valid_daily_rows: List[Dict[str, Any]] = []
    for row in daily_rows:
        event_id = row.get("event_id")
        if not event_id:
            log_warning("ETL validate: rejected daily row — empty event_id", {"row": row})
            rejected_count += 1
            continue
        sale_date = row.get("sale_date")
        if sale_date is not None:
            if isinstance(sale_date, str):
                try:
                    sale_date = datetime.fromisoformat(sale_date).date()
                except Exception:
                    sale_date = None
            if isinstance(sale_date, datetime):
                sale_date = sale_date.date()
            if isinstance(sale_date, date) and sale_date > today + __import__("datetime").timedelta(days=1):
                log_warning(
                    "ETL validate: rejected daily row — sale_date is in the future",
                    {"row": row},
                )
                rejected_count += 1
                continue
        valid_daily_rows.append(row)

    return valid_event_rows, valid_daily_rows, rejected_count


# ---------------------------------------------------------------------------
# ETL run log cursor helpers  (issue #161)
# ---------------------------------------------------------------------------

_ETL_RUN_LOG_TABLE = "etl_run_log"


def _ensure_run_log_table(engine: Engine) -> Table:
    """Create etl_run_log table if it does not exist and return the Table object."""
    metadata = MetaData()
    run_log = Table(
        _ETL_RUN_LOG_TABLE,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("started_at", TIMESTAMP(timezone=False)),
        Column("finished_at", TIMESTAMP(timezone=False)),
        Column("status", String),        # 'success' | 'failed'
        Column("last_run_at", TIMESTAMP(timezone=False)),
        Column("rejected_count", Integer),
    )
    with engine.begin() as conn:
        metadata.create_all(conn)  # type: ignore[arg-type]
    return run_log


def _load_last_successful_cursor(engine: Engine) -> Optional[str]:
    """Return the ISO-8601 ``finished_at`` of the last successful ETL run, or None."""
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    f"SELECT finished_at FROM {_ETL_RUN_LOG_TABLE} "  # noqa: S608
                    "WHERE status = 'success' "
                    "ORDER BY finished_at DESC "
                    "LIMIT 1"
                )
            ).fetchone()
        if row and row[0]:
            ts = row[0]
            if isinstance(ts, datetime):
                return ts.isoformat()
            return str(ts)
    except Exception as exc:
        logger.warning("Could not read ETL run log cursor: %s", exc)
    return None


def _save_run_log(
    engine: Engine,
    run_log_table: Table,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    rejected_count: int = 0,
) -> None:
    """Insert a row into etl_run_log."""
    try:
        with engine.begin() as conn:
            conn.execute(
                run_log_table.insert().values(
                    started_at=started_at,
                    finished_at=finished_at,
                    status=status,
                    last_run_at=finished_at if status == "success" else None,
                    rejected_count=rejected_count,
                )
            )
    except Exception as exc:
        logger.error("Failed to write ETL run log: %s", exc)


def transform_summary(
    events: List[Dict[str, Any]],
    sales: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Aggregate raw event and sales records into two summary table shapes.

    Returns:
        (event_summary_rows, daily_rows)
    """
    event_name_by_id: Dict[str, str] = {}
    for e in events:
        eid = str(e.get("id") or e.get("event_id") or "")
        if not eid:
            continue
        event_name_by_id[eid] = str(e.get("name") or e.get("title") or "")

    totals: Dict[str, Dict[str, Any]] = {}
    daily: Dict[Tuple[str, date], Dict[str, Any]] = {}

    for s in sales:
        eid = str(s.get("event_id") or s.get("eventId") or s.get("event") or "")
        if not eid:
            continue
        qty = _safe_int(s.get("quantity") or s.get("qty") or 1)
        price = _safe_float(s.get("price") or s.get("unit_price") or s.get("amount") or 0)
        total_amount = _safe_float(s.get("total_amount") or (qty * price))
        sd_raw = s.get("sale_date") or s.get("created_at") or s.get("timestamp")
        try:
            sd: date = datetime.fromisoformat(str(sd_raw)).date() if sd_raw else date.today()
        except Exception:
            sd = date.today()

        t = totals.setdefault(eid, {"event_id": eid, "total_tickets": 0, "total_revenue": 0.0})
        t["total_tickets"] += qty
        t["total_revenue"] += total_amount

        dkey = (eid, sd)
        d = daily.setdefault(dkey, {"event_id": eid, "sale_date": sd, "tickets_sold": 0, "revenue": 0.0})
        d["tickets_sold"] += qty
        d["revenue"] += total_amount

    now = datetime.utcnow()
    event_summary_rows: List[Dict[str, Any]] = []
    for eid, agg in totals.items():
        event_summary_rows.append({
            "event_id": eid,
            "event_name": event_name_by_id.get(eid, ""),
            "total_tickets": agg["total_tickets"],
            "total_revenue": float(agg["total_revenue"]),
            "last_updated": now,
        })

    daily_rows: List[Dict[str, Any]] = list(daily.values())
    for r in daily_rows:
        r["revenue"] = float(r["revenue"])

    return event_summary_rows, daily_rows


# ---------------------------------------------------------------------------
# Load — PostgreSQL
# ---------------------------------------------------------------------------

def _pg_engine() -> Optional[Engine]:
    url = get_settings().DATABASE_URL
    if not url:
        return None
    try:
        return create_engine(url, pool_pre_ping=True)
    except Exception as exc:
        logger.error("Failed to create PG engine: %s", exc)
        return None


def load_postgres(
    event_summary_rows: List[Dict[str, Any]],
    daily_rows: List[Dict[str, Any]],
) -> None:
    """Upsert event_summary and daily_ticket_sales rows into PostgreSQL."""
    engine = _pg_engine()
    if engine is None:
        logger.info("DATABASE_URL not set; skipping Postgres load")
        return

    metadata = MetaData()
    event_sales_summary = Table(
        "event_sales_summary",
        metadata,
        Column("event_id", String, primary_key=True),
        Column("event_name", String),
        Column("total_tickets", Integer),
        Column("total_revenue", Numeric(18, 2)),
        Column("last_updated", TIMESTAMP(timezone=False)),
    )
    daily_ticket_sales = Table(
        "daily_ticket_sales",
        metadata,
        Column("event_id", String, primary_key=True),
        Column("sale_date", Date, primary_key=True),
        Column("tickets_sold", Integer),
        Column("revenue", Numeric(18, 2)),
    )

    with engine.begin() as conn:
        metadata.create_all(conn)  # type: ignore[arg-type]

        if event_summary_rows:
            stmt = pg_insert(event_sales_summary).values(event_summary_rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=[event_sales_summary.c.event_id],
                set_={
                    "event_name": stmt.excluded.event_name,
                    "total_tickets": stmt.excluded.total_tickets,
                    "total_revenue": stmt.excluded.total_revenue,
                    "last_updated": stmt.excluded.last_updated,
                },
            )
            conn.execute(stmt)

        if daily_rows:
            stmt2 = pg_insert(daily_ticket_sales).values(daily_rows)
            stmt2 = stmt2.on_conflict_do_update(
                index_elements=[daily_ticket_sales.c.event_id, daily_ticket_sales.c.sale_date],
                set_={
                    "tickets_sold": stmt2.excluded.tickets_sold,
                    "revenue": stmt2.excluded.revenue,
                },
            )
            conn.execute(stmt2)

    log_info(
        "ETL load completed",
        {
            "database": "PostgreSQL",
            "event_summary_count": len(event_summary_rows),
            "daily_sales_count": len(daily_rows),
        },
    )


# ---------------------------------------------------------------------------
# Load — BigQuery (optional)
# ---------------------------------------------------------------------------

def load_bigquery(
    event_summary_rows: List[Dict[str, Any]],
    daily_rows: List[Dict[str, Any]],
) -> None:
    """Stream event_summary and daily_ticket_sales rows into BigQuery (optional)."""
    settings = get_settings()
    if not settings.BQ_ENABLED:
        return
    if bigquery is None:
        logger.warning("google-cloud-bigquery not available; skipping BigQuery load")
        return

    project_id = settings.BQ_PROJECT_ID
    dataset_id = settings.BQ_DATASET or "veritix"
    table_ev = settings.BQ_TABLE_EVENT_SUMMARY
    table_daily = settings.BQ_TABLE_DAILY_SALES

    if not project_id:
        logger.warning("BQ_PROJECT_ID not set; skipping BigQuery load")
        return

    client = bigquery.Client(project=project_id)

    from google.cloud.exceptions import NotFound  # type: ignore[import-untyped]  # noqa: PLC0415

    try:
        client.get_dataset(bigquery.DatasetReference(project_id, dataset_id))
    except NotFound:
        ds = bigquery.Dataset(f"{project_id}.{dataset_id}")
        ds.location = settings.BQ_LOCATION or "US"
        client.create_dataset(ds, exists_ok=True)

    def _ensure_table(table_name: str, schema: List[Any]) -> str:
        table_id = f"{project_id}.{dataset_id}.{table_name}"
        try:
            client.get_table(table_id)
        except NotFound:
            tbl = bigquery.Table(table_id, schema=schema)
            client.create_table(tbl)
        return table_id

    ev_schema = [
        bigquery.SchemaField("event_id", "STRING"),
        bigquery.SchemaField("event_name", "STRING"),
        bigquery.SchemaField("total_tickets", "INTEGER"),
        bigquery.SchemaField("total_revenue", "NUMERIC"),
        bigquery.SchemaField("last_updated", "TIMESTAMP"),
    ]
    daily_schema = [
        bigquery.SchemaField("event_id", "STRING"),
        bigquery.SchemaField("sale_date", "DATE"),
        bigquery.SchemaField("tickets_sold", "INTEGER"),
        bigquery.SchemaField("revenue", "NUMERIC"),
    ]

    ev_table_id = _ensure_table(table_ev, ev_schema)
    daily_table_id = _ensure_table(table_daily, daily_schema)

    ev_rows: List[Dict[str, Any]] = [
        {
            **row,
            "last_updated": (
                row["last_updated"].isoformat()
                if isinstance(row.get("last_updated"), datetime)
                else row.get("last_updated")
            ),
        }
        for row in event_summary_rows
    ]
    daily_rows_json: List[Dict[str, Any]] = [
        {
            **row,
            "sale_date": (
                row["sale_date"].isoformat()
                if isinstance(row.get("sale_date"), date)
                else row.get("sale_date")
            ),
        }
        for row in daily_rows
    ]

    errors1 = client.insert_rows_json(ev_table_id, ev_rows)
    errors2 = client.insert_rows_json(daily_table_id, daily_rows_json)

    if errors1:
        log_error("BigQuery load errors (event summary)", {"errors": errors1})
    if errors2:
        log_error("BigQuery load errors (daily sales)", {"errors": errors2})

    log_info(
        "ETL load completed",
        {
            "database": "BigQuery",
            "event_summary_count": len(ev_rows),
            "daily_sales_count": len(daily_rows_json),
        },
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_etl_once() -> None:
    """Run a single full ETL cycle: extract → transform → validate → load."""
    started_at = datetime.utcnow()
    log_info("ETL job started")

    # --- Cursor: load last successful run timestamp (issue #161) ---
    engine = _pg_engine()
    run_log_table: Optional[Table] = None
    since: Optional[str] = None
    if engine is not None:
        try:
            run_log_table = _ensure_run_log_table(engine)
            since = _load_last_successful_cursor(engine)
        except Exception as exc:
            log_error("Failed to initialise ETL run log", {"error": str(exc)})

    log_info("ETL extract cursor", {"since": since})

    rejected_count = 0
    status = "failed"
    try:
        events, sales = extract_events_and_sales(since=since)
        ev_rows, daily_rows = transform_summary(
            [event.raw for event in events],
            [sale.raw for sale in sales],
        )

        # --- Validation step (issue #162) ---
        ev_rows, daily_rows, rejected_count = validate_rows(ev_rows, daily_rows)
        if rejected_count:
            log_warning(
                "ETL validation rejected rows",
                {"rejected_count": rejected_count},
            )

        try:
            load_postgres(ev_rows, daily_rows)
        except Exception as exc:
            log_error("Postgres load failed", {"error": str(exc)})
            raise
        try:
            load_bigquery(ev_rows, daily_rows)
        except Exception as exc:
            log_error("BigQuery load failed", {"error": str(exc)})

        status = "success"
    finally:
        finished_at = datetime.utcnow()
        if engine is not None and run_log_table is not None:
            _save_run_log(
                engine,
                run_log_table,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                rejected_count=rejected_count,
            )
        log_info("ETL job completed", {"status": status, "rejected_count": rejected_count})