import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime, date

from sqlalchemy import create_engine, Table, Column, MetaData, String, Integer, Numeric, Date, TIMESTAMP
from sqlalchemy.dialects.postgresql import insert as pg_insert

try:
    from google.cloud import bigquery  # type: ignore
except Exception:
    bigquery = None  # Optional dependency

from src.logging_config import log_info, log_error, ETL_JOBS_TOTAL
from src.config import get_settings
from .extract import extract_events_and_sales

logger = logging.getLogger("veritix.etl")


# -----------------------
# Transform
# -----------------------
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


def transform_summary(events: List[Dict[str, Any]], sales: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    # Map event_id -> name for join
    event_name_by_id: Dict[str, str] = {}
    for e in events:
        eid = str(e.get("id") or e.get("event_id") or "")
        if not eid:
            continue
        name = str(e.get("name") or e.get("title") or "")
        event_name_by_id[eid] = name

    # Aggregate totals by event
    totals: Dict[str, Dict[str, Any]] = {}
    daily: Dict[Tuple[str, date], Dict[str, Any]] = {}
    for s in sales:
        eid = str(s.get("event_id") or s.get("eventId") or s.get("event") or "")
        if not eid:
            continue
        qty = _safe_int(s.get("quantity") or s.get("qty") or 1)
        price = _safe_float(s.get("price") or s.get("unit_price") or s.get("amount") or 0)
        total_amount = _safe_float(s.get("total_amount") or (qty * price))
        # sale_date may be ISO string; fallback to today
        sd_raw = s.get("sale_date") or s.get("created_at") or s.get("timestamp")
        try:
            sd = datetime.fromisoformat(str(sd_raw)).date() if sd_raw else date.today()
        except Exception:
            sd = date.today()

        t = totals.setdefault(eid, {"event_id": eid, "total_tickets": 0, "total_revenue": 0.0})
        t["total_tickets"] += qty
        t["total_revenue"] += total_amount

        dkey = (eid, sd)
        d = daily.setdefault(dkey, {"event_id": eid, "sale_date": sd, "tickets_sold": 0, "revenue": 0.0})
        d["tickets_sold"] += qty
        d["revenue"] += total_amount

    # Build rows with event_name
    now = datetime.utcnow()
    event_summary_rows = []
    for eid, agg in totals.items():
        event_summary_rows.append({
            "event_id": eid,
            "event_name": event_name_by_id.get(eid, ""),
            "total_tickets": agg["total_tickets"],
            "total_revenue": float(agg["total_revenue"]),
            "last_updated": now,
        })

    daily_rows = list(daily.values())
    # Ensure revenue is float
    for r in daily_rows:
        r["revenue"] = float(r["revenue"])

    return event_summary_rows, daily_rows


# -----------------------
# Load (Postgres)
# -----------------------
def _pg_engine():
    url = get_settings().DATABASE_URL
    try:
        engine = create_engine(url, pool_pre_ping=True)
        return engine
    except Exception as exc:
        logger.error("Failed to create PG engine: %s", exc)
        return None


def load_postgres(event_summary_rows: List[Dict[str, Any]], daily_rows: List[Dict[str, Any]]) -> None:
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
        metadata.create_all(conn)
        # Upsert event_sales_summary
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
        # Upsert daily_ticket_sales
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
    log_info("ETL load completed", {
        "database": "PostgreSQL",
        "event_summary_count": len(event_summary_rows),
        "daily_sales_count": len(daily_rows)
    })


# -----------------------
# Load (BigQuery optional)
# -----------------------
def load_bigquery(event_summary_rows: List[Dict[str, Any]], daily_rows: List[Dict[str, Any]]) -> None:
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
    # Ensure dataset exists
    from google.cloud.exceptions import NotFound  # type: ignore
    try:
        dataset_ref = client.get_dataset(bigquery.DatasetReference(project_id, dataset_id))
    except NotFound:
        dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
        dataset.location = settings.BQ_LOCATION or "US"
        dataset_ref = client.create_dataset(dataset, exists_ok=True)

    def _ensure_table(table_name: str, schema: List[bigquery.SchemaField]):
        table_id = f"{project_id}.{dataset_id}.{table_name}"
        try:
            client.get_table(table_id)
        except NotFound:
            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table)
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

    # Convert timestamps/dates to RFC3339/ISO strings for BigQuery JSON
    ev_rows = [
        {
            **row,
            "last_updated": (row["last_updated"].isoformat() if isinstance(row.get("last_updated"), datetime) else row.get("last_updated")),
        }
        for row in event_summary_rows
    ]
    daily_rows_json = [
        {
            **row,
            "sale_date": (row["sale_date"].isoformat() if isinstance(row.get("sale_date"), date) else row.get("sale_date")),
        }
        for row in daily_rows
    ]

    errors1 = client.insert_rows_json(ev_table_id, ev_rows)
    errors2 = client.insert_rows_json(daily_table_id, daily_rows_json)
    if errors1:
        log_error("BigQuery load errors (event summary)", {"errors": errors1})
    if errors2:
        log_error("BigQuery load errors (daily sales)", {"errors": errors2})
    log_info("ETL load completed", {
        "database": "BigQuery",
        "event_summary_count": len(ev_rows),
        "daily_sales_count": len(daily_rows_json)
    })


# -----------------------
# Orchestration
# -----------------------
def run_etl_once() -> None:
    log_info("ETL job started")
    events, sales = extract_events_and_sales()
    ev_rows, daily_rows = transform_summary(
        [event.raw for event in events],
        [sale.raw for sale in sales],
    )
    try:
        load_postgres(ev_rows, daily_rows)
    except Exception as exc:
        log_error("Postgres load failed", {"error": str(exc)})
    try:
        load_bigquery(ev_rows, daily_rows)
    except Exception as exc:
        log_error("BigQuery load failed", {"error": str(exc)})
    log_info("ETL job completed")
