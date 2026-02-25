import csv
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import Engine, create_engine, text

from src.config import get_settings

logger = logging.getLogger("veritix.report_service")

REPORTS_DIR = Path("reports")


def _pg_engine() -> Optional[Engine]:
    url = get_settings().DATABASE_URL
    if not url:
        logger.info("DATABASE_URL not set; skipping Postgres engine creation")
        return None
    try:
        engine = create_engine(url, pool_pre_ping=True)
        return engine
    except Exception as exc:
        logger.error("Failed to create PG engine: %s", exc)
        return None


def _ensure_reports_dir() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)


def _query_daily_sales(target_date: Optional[date] = None) -> List[Dict[str, Any]]:
    engine = _pg_engine()
    if engine is None:
        logger.warning("DATABASE_URL not set; cannot query sales data")
        return []

    if target_date is None:
        target_date = date.today()

    query = text("""
        SELECT
            event_id,
            sale_date,
            tickets_sold,
            revenue
        FROM daily_ticket_sales
        WHERE sale_date = :target_date
        ORDER BY event_id
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"target_date": target_date})
        rows: List[Dict[str, Any]] = []
        for row in result:
            rows.append({
                "event_id": row[0],
                "sale_date": str(row[1]),
                "tickets_sold": row[2],
                "revenue": float(row[3]) if row[3] is not None else 0.0,
            })
        return rows


def _query_event_names() -> Dict[str, str]:
    engine = _pg_engine()
    if engine is None:
        return {}

    query = text("""
        SELECT event_id, event_name
        FROM event_sales_summary
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        return {row[0]: row[1] for row in result}


def _query_transfer_stats(target_date: Optional[date] = None) -> Dict[str, int]:
    """Query transfer statistics.

    Returns a placeholder dict; a real implementation would query a transfers table.
    """
    return {"total_transfers": 0}


def _query_invalid_scans(target_date: Optional[date] = None) -> Dict[str, int]:
    """Query invalid scan statistics.

    Returns a placeholder dict; a real implementation would query a scans table.
    """
    return {"invalid_scans": 0}


def generate_daily_report_csv(
    target_date: Optional[date] = None,
    output_format: str = "csv",
) -> str:
    """Generate a daily sales report as CSV or JSON.

    Returns the path to the generated file as a string.
    """
    if target_date is None:
        target_date = date.today()

    _ensure_reports_dir()

    sales_data = _query_daily_sales(target_date)
    event_names = _query_event_names()
    transfer_stats = _query_transfer_stats(target_date)
    invalid_scan_stats = _query_invalid_scans(target_date)

    total_sales: int = sum(row["tickets_sold"] for row in sales_data)
    total_revenue: float = sum(row["revenue"] for row in sales_data)
    total_transfers: int = transfer_stats.get("total_transfers", 0)
    invalid_scans: int = invalid_scan_stats.get("invalid_scans", 0)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if output_format == "json":
        filename = f"daily_report_{target_date}_{timestamp}.json"
        filepath = REPORTS_DIR / filename

        report_data: Dict[str, Any] = {
            "report_date": str(target_date),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "total_transfers": total_transfers,
                "invalid_scans": invalid_scans,
            },
            "sales_by_event": [
                {**row, "event_name": event_names.get(row["event_id"], "Unknown")}
                for row in sales_data
            ],
        }

        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info("Generated JSON report: %s", filepath)
        return str(filepath)

    # CSV format (default)
    filename = f"daily_report_{target_date}_{timestamp}.csv"
    filepath = REPORTS_DIR / filename

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Daily Sales Report"])
        writer.writerow(["Report Date", str(target_date)])
        writer.writerow(["Generated At", datetime.utcnow().isoformat()])
        writer.writerow([])
        writer.writerow(["Summary"])
        writer.writerow(["Total Sales", total_sales])
        writer.writerow(["Total Revenue", f"${total_revenue:.2f}"])
        writer.writerow(["Total Transfers", total_transfers])
        writer.writerow(["Invalid Scans", invalid_scans])
        writer.writerow([])
        writer.writerow(["Sales by Event"])
        writer.writerow(["Event ID", "Event Name", "Sale Date", "Tickets Sold", "Revenue"])

        for row in sales_data:
            writer.writerow([
                row["event_id"],
                event_names.get(row["event_id"], "Unknown"),
                row["sale_date"],
                row["tickets_sold"],
                f"${row['revenue']:.2f}",
            ])

    logger.info("Generated CSV report: %s", filepath)
    return str(filepath)