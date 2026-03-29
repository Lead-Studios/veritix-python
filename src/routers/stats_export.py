"""Router for /stats/export — stream analytics data as a downloadable CSV."""
import csv
import io
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from src.analytics.service import analytics_service

router = APIRouter(tags=["Analytics"])


@router.get("/stats/export")
def export_stats(event_id: Optional[str] = Query(default=None, description="Filter by event ID")):
    """Stream analytics stats as a downloadable CSV file.

    If event_id is provided, exports stats for that event only.
    Otherwise exports stats for all events.
    """
    if event_id:
        raw = analytics_service.get_stats_for_event(event_id)
        rows = [raw]
    else:
        all_stats = analytics_service.get_stats_for_all_events()
        rows = list(all_stats.values())

    output = io.StringIO()
    if not rows:
        output.write("No data available\n")
    else:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    output.seek(0)

    filename = f"stats_{event_id}.csv" if event_id else "stats_all_events.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
