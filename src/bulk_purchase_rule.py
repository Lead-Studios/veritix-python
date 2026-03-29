"""Fraud rule: bulk purchase detection — same card/user buying entire ticket allocation.

A purchase is flagged when a single user or card accounts for a threshold percentage
(default 20%) of an event's total ticket capacity in a single transaction or cumulatively.
"""
from typing import Any, Dict, List

BULK_PURCHASE_THRESHOLD = 0.20  # 20% of event capacity


def check_bulk_purchase(
    events: List[Dict[str, Any]],
    threshold: float = BULK_PURCHASE_THRESHOLD,
) -> bool:
    """Return True if any user/card purchased >= threshold of an event's capacity.

    Accumulates purchase quantities per (user, event_id) pair and compares the
    total against the event capacity supplied on each purchase event.
    """
    # Accumulate quantities per (user, event_id)
    totals: Dict[tuple, float] = {}
    capacities: Dict[str, float] = {}

    for event in events:
        if event.get("type") != "purchase":
            continue

        event_id = str(event.get("event_id", ""))
        user = str(event.get("user", event.get("card", "")))
        qty = float(event.get("qty", 1))
        capacity = float(event.get("capacity", 0))

        if capacity > 0:
            capacities[event_id] = capacity

        key = (user, event_id)
        totals[key] = totals.get(key, 0.0) + qty

    for (user, event_id), total_qty in totals.items():
        capacity = capacities.get(event_id, 0.0)
        if capacity > 0 and (total_qty / capacity) >= threshold:
            return True

    return False
