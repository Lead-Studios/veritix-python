from typing import List, Dict, Any
from datetime import datetime, timedelta

# --- Example Fraud Detection Rules ---
# 1. Too many purchases from same IP in a short window (e.g., >3 in 10min)
# 2. Duplicate ticket transfers (same ticket transferred more than once)
# 3. Excessive purchases by same user in a day (e.g., >5)

def check_fraud_rules(events: List[Dict[str, Any]]) -> List[str]:
    triggered = set()
    # Rule 1: Too many purchases from same IP in 10min (>3)
    purchases_by_ip = {}
    for event in events:
        if event.get("type") == "purchase":
            ip = event.get("ip")
            ts = datetime.fromisoformat(event.get("timestamp"))
            purchases_by_ip.setdefault(ip, []).append(ts)
    for ip, times in purchases_by_ip.items():
        times.sort()
        for i in range(len(times)):
            window = [t for t in times if 0 <= (t - times[i]).total_seconds() <= 600]
            if len(window) > 3:
                triggered.add("too_many_purchases_same_ip")
                break
    # Rule 2: Duplicate ticket transfers (same ticket transferred more than once)
    transfer_counts = {}
    for event in events:
        if event.get("type") == "transfer":
            tid = event.get("ticket_id")
            transfer_counts[tid] = transfer_counts.get(tid, 0) + 1
    for tid, count in transfer_counts.items():
        if count > 1:
            triggered.add("duplicate_ticket_transfer")
    # Rule 3: Excessive purchases by same user in a day (>5)
    purchases_by_user_day = {}
    for event in events:
        if event.get("type") == "purchase":
            user = event.get("user")
            day = datetime.fromisoformat(event.get("timestamp")).date()
            key = (user, day)
            purchases_by_user_day[key] = purchases_by_user_day.get(key, 0) + 1
    for key, count in purchases_by_user_day.items():
        if count > 5:
            triggered.add("excessive_purchases_user_day")
    return list(triggered)


def determine_severity(triggered_rules: List[str]) -> str:
    """Map triggered fraud rule IDs to a simple severity level.

    Returns one of: 'none' (no rules), 'low', 'medium', 'high'.

    Logic (simple heuristic):
    - If any rule in HIGH_RULES is present -> 'high'
    - Else if any rule in MEDIUM_RULES -> 'medium'
    - Else if there are any triggered rules -> 'low'
    - Else -> 'none'
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
