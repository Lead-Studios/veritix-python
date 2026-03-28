import csv
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

import src.db as _db

logger = logging.getLogger("veritix.report_service")

REPORTS_DIR = Path("reports")

# ---------------------------------------------------------------------------
# generated_reports table helpers
# ---------------------------------------------------------------------------

_FILENAME_RE = re.compile(r"^daily_report_(\d{4}-\d{2}-\d{2})_\d{8}_\d{6}\.(csv|json)$")


def create_generated_reports_table() -> None:
    """Create the generated_reports table if it does not yet exist."""
    engine = _pg_engine()
    if engine is None:
        logger.info("Skipping generated_reports table creation — no DB engine")
        return
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_reports (
                id          SERIAL PRIMARY KEY,
                filename    TEXT        NOT NULL UNIQUE,
                report_date DATE        NOT NULL,
                format      TEXT        NOT NULL,
                size_bytes  BIGINT      NOT NULL,
                generated_at TIMESTAMP  NOT NULL
            )
        """))
    logger.info("generated_reports table ready")


def insert_report_metadata(
    filename: str,
    report_date: date,
    fmt: str,
    size_bytes: int,
    generated_at: datetime,
) -> None:
    """Insert a single report row, silently ignoring duplicate filenames."""
    engine = _pg_engine()
    if engine is None:
        return
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO generated_reports (filename, report_date, format, size_bytes, generated_at)
                VALUES (:filename, :report_date, :format, :size_bytes, :generated_at)
                ON CONFLICT (filename) DO NOTHING
            """),
            {
                "filename": filename,
                "report_date": report_date,
                "format": fmt,
                "size_bytes": size_bytes,
                "generated_at": generated_at,
            },
        )


def list_reports() -> List[Dict[str, Any]]:
    """Return up to 100 most recently generated reports from the DB."""
    engine = _pg_engine()
    if engine is None:
        return []
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT filename, report_date, format, size_bytes, generated_at
            FROM generated_reports
            ORDER BY generated_at DESC
            LIMIT 100
        """))
        rows: List[Dict[str, Any]] = []
        for row in result:
            filename = row[0]
            rows.append({
                "filename": filename,
                "report_date": str(row[1]),
                "format": row[2],
                "size_bytes": row[3],
                "generated_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                "download_url": f"/reports/download/{filename}",
            })
        return rows


def scan_and_populate_reports() -> None:
    """Scan the reports/ directory and insert metadata for any file not yet in the DB."""
    engine = _pg_engine()
    if engine is None:
        return
    _ensure_reports_dir()
    for filepath in sorted(REPORTS_DIR.iterdir()):
        if not filepath.is_file():
            continue
        m = _FILENAME_RE.match(filepath.name)
        if not m:
            continue
        try:
            report_date = date.fromisoformat(m.group(1))
            fmt = m.group(2)
            size_bytes = filepath.stat().st_size
            # Use file modification time as a best-effort generated_at
            generated_at = datetime.utcfromtimestamp(filepath.stat().st_mtime)
            insert_report_metadata(filepath.name, report_date, fmt, size_bytes, generated_at)
        except Exception as exc:
            logger.warning("Skipping %s during scan: %s", filepath.name, exc)
    logger.info("reports/ directory scan complete")


# ---------------------------------------------------------------------------
# generated_reports table helpers
# ---------------------------------------------------------------------------

def create_generated_reports_table() -> None:
    """Create the generated_reports table if it does not yet exist."""
    engine = _pg_engine()
    if engine is None:
        logger.info("Skipping generated_reports table creation — no DB engine")
        return
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_reports (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                report_date DATE NOT NULL,
                event_id TEXT,
                format TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                generated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.commit()
    logger.info("generated_reports table ready")


def insert_report_metadata(
    filename: str,
    report_date: date,
    event_id: Optional[str],
    fmt: str,
    size_bytes: int,
    generated_at: datetime,
) -> None:
    """Insert a row into generated_reports after a file is written."""
    engine = _pg_engine()
    if engine is None:
        return
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO generated_reports
                    (filename, report_date, event_id, format, size_bytes, generated_at)
                VALUES
                    (:filename, :report_date, :event_id, :format, :size_bytes, :generated_at)
            """),
            {
                "filename": filename,
                "report_date": report_date,
                "event_id": event_id,
                "format": fmt,
                "size_bytes": size_bytes,
                "generated_at": generated_at,
            },
        )
        conn.commit()


def check_report_cache(
    report_date: date,
    event_id: Optional[str],
    fmt: str,
    cache_minutes: int,
) -> Optional[Dict[str, Any]]:
    """Return metadata for the most recent matching cached report, or None."""
    engine = _pg_engine()
    if engine is None:
        return None
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT filename, size_bytes, generated_at
                FROM generated_reports
                WHERE report_date = :report_date
                  AND format = :format
                  AND (
                      (:event_id IS NULL AND event_id IS NULL)
                      OR event_id = :event_id
                  )
                  AND generated_at >= NOW() - (:cache_minutes || ' minutes')::INTERVAL
                ORDER BY generated_at DESC
                LIMIT 1
            """),
            {
                "report_date": report_date,
                "event_id": event_id,
                "format": fmt,
                "cache_minutes": cache_minutes,
            },
        )
        row = result.fetchone()
    if row is None:
        return None
    return {
        "filename": row[0],
        "size_bytes": row[1],
        "generated_at": row[2],
    }


def _pg_engine():
    return _db.get_engine()


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
    engine = _pg_engine()
    if engine is None:
        logger.warning("DATABASE_URL not set; cannot query transfer stats")
        return {"total_transfers": 0}

    if target_date is None:
        target_date = date.today()

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM ticket_transfers WHERE transfer_timestamp::date = :target_date"),
            {"target_date": target_date},
        )
        row = result.fetchone()
    return {"total_transfers": int(row[0]) if row else 0}


def _query_invalid_scans(target_date: Optional[date] = None) -> Dict[str, int]:
    engine = _pg_engine()
    if engine is None:
        logger.warning("DATABASE_URL not set; cannot query invalid scan stats")
        return {"invalid_scans": 0}

    if target_date is None:
        target_date = date.today()

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM invalid_attempts WHERE attempt_timestamp::date = :target_date"),
            {"target_date": target_date},
        )
        row = result.fetchone()
    return {"invalid_scans": int(row[0]) if row else 0}


def generate_daily_report_csv(
    target_date: Optional[date] = None,
    output_format: str = "csv",
    event_id: Optional[str] = None,
    force_regenerate: bool = False,
    cache_minutes: int = 60,
) -> Tuple[str, bool]:
    """Generate a daily sales report as CSV or JSON.

    Returns (path_to_generated_file, cache_hit).
    When cache_hit is True the file already existed and was not regenerated.
    """
    if target_date is None:
        target_date = date.today()

    # --- cache check ---
    if not force_regenerate:
        cached = check_report_cache(target_date, event_id, output_format, cache_minutes)
        if cached is not None:
            cached_path = str(REPORTS_DIR / cached["filename"])
            if Path(cached_path).exists():
                logger.info("Cache hit — returning existing report %s", cached["filename"])
                return cached_path, True

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

        size_bytes = filepath.stat().st_size
        now = datetime.utcnow()
        insert_report_metadata(filename, report_date=target_date, event_id=event_id,
                               fmt="json", size_bytes=size_bytes, generated_at=now)
        generated_at = datetime.utcnow()
        insert_report_metadata(
            filename=filename,
            report_date=target_date,
            fmt="json",
            size_bytes=filepath.stat().st_size,
            generated_at=generated_at,
        )
        logger.info("Generated JSON report: %s", filepath)
        return str(filepath), False

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

    size_bytes = filepath.stat().st_size
    now = datetime.utcnow()
    insert_report_metadata(filename, report_date=target_date, event_id=event_id,
                           fmt="csv", size_bytes=size_bytes, generated_at=now)
    generated_at = datetime.utcnow()
    insert_report_metadata(
        filename=filename,
        report_date=target_date,
        fmt="csv",
        size_bytes=filepath.stat().st_size,
        generated_at=generated_at,
    )
    logger.info("Generated CSV report: %s", filepath)
    return str(filepath), False