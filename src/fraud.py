from datetime import datetime
from typing import Any, Dict, List


def check_fraud_rules(events: List[Dict[str, Any]]) -> List[str]:
    """Evaluate a list of ticket events against fraud detection rules.

    Returns a list of triggered rule names.
    """
    triggered: set[str] = set()

    # Rule 1: Too many purchases from same IP in 10 min (>3)
    purchases_by_ip: Dict[str, List[datetime]] = {}
    for event in events:
        if event.get("type") == "purchase":
            ip: str = str(event.get("ip", ""))
            ts = datetime.fromisoformat(str(event.get("timestamp", "")))
            purchases_by_ip.setdefault(ip, []).append(ts)
    for _ip, times in purchases_by_ip.items():
        times.sort()
        for i in range(len(times)):
            window = [t for t in times if 0 <= (t - times[i]).total_seconds() <= 600]
            if len(window) > 3:
                triggered.add("too_many_purchases_same_ip")
                break

    # Rule 2: Duplicate ticket transfers (same ticket transferred more than once)
    transfer_counts: Dict[str, int] = {}
    for event in events:
        if event.get("type") == "transfer":
            tid: str = str(event.get("ticket_id", ""))
            transfer_counts[tid] = transfer_counts.get(tid, 0) + 1
    for _tid, count in transfer_counts.items():
        if count > 1:
            triggered.add("duplicate_ticket_transfer")

    # Rule 3: Excessive purchases by same user in a day (>5)
    from datetime import date as date_type  # noqa: PLC0415 – local import to avoid shadowing
    purchases_by_user_day: Dict[tuple[str, date_type], int] = {}
    for event in events:
        if event.get("type") == "purchase":
            user: str = str(event.get("user", ""))
            day = datetime.fromisoformat(str(event.get("timestamp", ""))).date()
            key = (user, day)
            purchases_by_user_day[key] = purchases_by_user_day.get(key, 0) + 1
    for _key, count in purchases_by_user_day.items():
        if count > 5:
            triggered.add("excessive_purchases_user_day")

    return list(triggered)


def determine_severity(triggered_rules: List[str]) -> str:
    """Map triggered fraud rule IDs to a simple severity level.

    Returns one of: 'none' (no rules), 'low', 'medium', 'high'.
    """
    if not triggered_rules:
        return "none"

    HIGH_RULES = {"too_many_purchases_same_ip", "excessive_purchases_user_day"}
    MEDIUM_RULES = {"duplicate_ticket_transfer"}

    s = set(triggered_rules)
    if s & HIGH_RULES:
        return "high"
    if s & MEDIUM_RULES:
        return "medium"
    return "low"