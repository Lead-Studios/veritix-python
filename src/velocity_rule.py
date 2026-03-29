"""Fraud rule: velocity check for the same ticket scanned at geographically impossible locations.

A ticket is flagged when it is scanned at two *different* named locations within a
configurable time window (default 30 minutes), which would require physically
impossible travel between venues.
"""
from datetime import datetime
from typing import Any, Dict, List

# Maximum seconds between two scans at different locations before flagging
IMPOSSIBLE_TRAVEL_WINDOW_SECONDS = 1800  # 30 minutes


def check_velocity_impossible_locations(
    events: List[Dict[str, Any]],
    window_seconds: int = IMPOSSIBLE_TRAVEL_WINDOW_SECONDS,
) -> bool:
    """Return True if any ticket was scanned at geographically impossible locations.

    Groups scan events by ticket_id, sorts them by timestamp, and checks
    consecutive pairs: if two scans occur at different locations within
    *window_seconds* the rule is triggered.
    """
    scans_by_ticket: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        if event.get("type") == "scan":
            tid = str(event.get("ticket_id", ""))
            scans_by_ticket.setdefault(tid, []).append(event)

    for scans in scans_by_ticket.values():
        scans.sort(key=lambda e: datetime.fromisoformat(str(e.get("timestamp", ""))))
        for i in range(len(scans) - 1):
            t1 = datetime.fromisoformat(str(scans[i].get("timestamp", "")))
            t2 = datetime.fromisoformat(str(scans[i + 1].get("timestamp", "")))
            loc1 = scans[i].get("location")
            loc2 = scans[i + 1].get("location")
            if loc1 and loc2 and loc1 != loc2:
                if (t2 - t1).total_seconds() <= window_seconds:
                    return True
    return False
