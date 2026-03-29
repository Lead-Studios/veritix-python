"""Extract ML training features from real analytics data instead of synthetic data.

Builds (X, y) arrays from TicketScan, TicketTransfer, and InvalidAttempt records
stored in the database so the scalper-detection model trains on actual behaviour.
"""
from typing import Any, List, Tuple

import numpy as np  # type: ignore[import-untyped]

from src.analytics.models import AnalyticsStats, InvalidAttempt, TicketScan, TicketTransfer, get_session
from sqlalchemy import func


def extract_features_from_analytics() -> Tuple[Any, Any]:
    """Return (X, y) arrays built from real analytics records.

    Features per event_id:
        0 - total scans
        1 - invalid scan rate  (invalid / total scans, or 0)
        2 - total transfers
        3 - failed transfer rate (failed / total transfers, or 0)
        4 - invalid attempt count

    Label: 1 (suspicious) when invalid_scan_rate > 0.3 or failed_transfer_rate > 0.5,
           0 otherwise.

    Falls back to an empty array pair if no data is available.
    """
    session = get_session()
    try:
        # Aggregate per event_id from AnalyticsStats
        stats = session.query(AnalyticsStats).all()

        if not stats:
            return np.empty((0, 5), dtype=float), np.empty((0,), dtype=int)

        rows: List[List[float]] = []
        labels: List[int] = []

        for s in stats:
            total_scans = max(s.scan_count, 1)
            total_transfers = max(s.transfer_count, 1)
            invalid_scan_rate = s.invalid_scan_count / total_scans
            failed_transfer_rate = s.failed_transfer_count / total_transfers

            features = [
                float(s.scan_count),
                invalid_scan_rate,
                float(s.transfer_count),
                failed_transfer_rate,
                float(s.invalid_attempt_count),
            ]
            label = int(invalid_scan_rate > 0.3 or failed_transfer_rate > 0.5)
            rows.append(features)
            labels.append(label)

        return np.array(rows, dtype=float), np.array(labels, dtype=int)
    finally:
        session.close()
