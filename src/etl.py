import os
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime, date

import httpx
from sqlalchemy import create_engine, Table, Column, MetaData, String, Integer, Numeric, Date, TIMESTAMP
from sqlalchemy.dialects.postgresql import insert as pg_insert

try:
    from google.cloud import bigquery  # type: ignore
except Exception:
    bigquery = None  # Optional dependency

logger = logging.getLogger("veritix.etl")


# -----------------------
# Extract
# -----------------------
def _auth_headers() -> Dict[str, str]:
    token = os.getenv("NEST_API_TOKEN")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def extract_events_and_sales() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    base_url = os.getenv("NEST_API_BASE_URL")
    if not base_url:
        logger.warning("NEST_API_BASE_URL not set; returning empty extract")
        return [], []
    events_url = base_url.rstrip("/") + "/events"
    sales_url = base_url.rstrip("/") + "/ticket-sales"
    headers = _auth_headers()
    try:
        with httpx.Client(timeout=30) as client:
            ev_resp = client.get(events_url, headers=headers)
            ev_resp.raise_for_status()
            events = ev_resp.json()
            ts_resp = client.get(sales_url, headers=headers)
            ts_resp.raise_for_status()
            sales = ts_resp.json()
            # Normalize to list
            if isinstance(events, dict):
                events = events.get("data", []) or []
            if isinstance(sales, dict):
                sales = sales.get("data", []) or []
            return events, sales
    except Exception as exc:
        logger.error("ETL extract failed: %s", exc)
        return [], []


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
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
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
    logger.info("Loaded %d events and %d daily sales into Postgres", len(event_summary_rows), len(daily_rows))


# -----------------------
# Load (BigQuery optional)
# -----------------------
def load_bigquery(event_summary_rows: List[Dict[str, Any]], daily_rows: List[Dict[str, Any]]) -> None:
    if os.getenv("BQ_ENABLED", "false").lower() not in ("true", "1", "yes"):
        return
    if bigquery is None:
        logger.warning("google-cloud-bigquery not available; skipping BigQuery load")
        return
    project_id = os.getenv("BQ_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET", "veritix")
    table_ev = os.getenv("BQ_TABLE_EVENT_SUMMARY", "event_sales_summary")
    table_daily = os.getenv("BQ_TABLE_DAILY_SALES", "daily_ticket_sales")
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
        dataset.location = os.getenv("BQ_LOCATION", "US")
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
        logger.error("BigQuery load errors (event summary): %s", errors1)
    if errors2:
        logger.error("BigQuery load errors (daily sales): %s", errors2)
    logger.info("Loaded rows into BigQuery: ev=%d, daily=%d", len(ev_rows), len(daily_rows_json))


# -----------------------
# Orchestration
# -----------------------
def run_etl_once() -> None:
    events, sales = extract_events_and_sales()
    ev_rows, daily_rows = transform_summary(events, sales)
    try:
        load_postgres(ev_rows, daily_rows)
    except Exception as exc:
        logger.error("Postgres load failed: %s", exc)
    try:
        load_bigquery(ev_rows, daily_rows)
    except Exception as exc:
        logger.error("BigQuery load failed: %s", exc)