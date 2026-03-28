"""Event store: loads events from Postgres event_sales_summary with a 60-second TTL cache."""
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import text

import src.db as _db
from src.logging_config import log_info

_cache: Optional[List[Dict[str, Any]]] = None
_cache_ts: float = 0.0
_CACHE_TTL = 60.0  # seconds


def get_events_from_db() -> List[Dict[str, Any]]:
    """Return events from Postgres event_sales_summary, cached for 60 s.

    Falls back to an empty list when the DB is unavailable.
    """
    global _cache, _cache_ts
    now = time.monotonic()
    if _cache is not None and (now - _cache_ts) < _CACHE_TTL:
        return _cache

    engine = _db.get_engine()
    if engine is None:
        return _cache or []

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT event_id, event_name, total_tickets, total_revenue, last_updated "
                    "FROM event_sales_summary"
                )
            ).fetchall()
        events: List[Dict[str, Any]] = [
            {
                "id": str(row[0]),
                "name": str(row[1] or ""),
                "description": "",
                "event_type": "general",
                "location": "",
                "date": row[4].isoformat() if row[4] else "",
                "price": float(row[3] or 0) / max(int(row[2] or 1), 1),
                "capacity": int(row[2] or 0),
            }
            for row in rows
        ]
        _cache = events
        _cache_ts = now
        log_info("event_store: loaded events from DB", {"count": len(events)})
        return events
    except Exception as exc:
        from src.logging_config import log_error
        log_error("event_store: DB query failed", {"error": str(exc)})
        return _cache or []


def invalidate_cache() -> None:
    """Force the next call to re-query the database."""
    global _cache, _cache_ts
    _cache = None
    _cache_ts = 0.0
