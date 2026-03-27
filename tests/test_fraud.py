import pytest
from datetime import datetime, timedelta
from src.fraud import check_fraud_rules, determine_severity

class TestFraudRules:
    """Unit tests for check_fraud_rules covering all 5 core rules and boundaries."""

    def test_too_many_purchases_same_ip(self):
        """Rule 1: >3 purchases from same IP in 10-min window."""
        base_ts = datetime(2025, 1, 1, 10, 0, 0)
        
        # 3 in window (no trigger)
        events_3 = [
            {"type": "purchase", "ip": "1.1.1.1", "timestamp": (base_ts + timedelta(minutes=i)).isoformat()}
            for i in range(3)
        ]
        assert "too_many_purchases_same_ip" not in check_fraud_rules(events_3)
        
        # 4 in window (trigger)
        events_4 = events_3 + [
            {"type": "purchase", "ip": "1.1.1.1", "timestamp": (base_ts + timedelta(seconds=240)).isoformat()}
        ]
        assert "too_many_purchases_same_ip" in check_fraud_rules(events_4)
        
        # 4 across two 10-min windows (no trigger)
        events_split = [
            {"type": "purchase", "ip": "2.2.2.2", "timestamp": base_ts.isoformat()},
            {"type": "purchase", "ip": "2.2.2.2", "timestamp": (base_ts + timedelta(seconds=10)).isoformat()},
            {"type": "purchase", "ip": "2.2.2.2", "timestamp": (base_ts + timedelta(seconds=601)).isoformat()},
            {"type": "purchase", "ip": "2.2.2.2", "timestamp": (base_ts + timedelta(seconds=610)).isoformat()},
        ]
        assert "too_many_purchases_same_ip" not in check_fraud_rules(events_split)

    def test_duplicate_ticket_transfer(self):
        """Rule 2: Same ticket_id transferred more than once."""
        # Single transfer (no trigger)
        assert "duplicate_ticket_transfer" not in check_fraud_rules([{"type": "transfer", "ticket_id": "T1"}])
        
        # Double transfer (trigger)
        events = [
            {"type": "transfer", "ticket_id": "T2"},
            {"type": "transfer", "ticket_id": "T2"},
        ]
        assert "duplicate_ticket_transfer" in check_fraud_rules(events)

    def test_excessive_purchases_user_day(self):
        """Rule 3: >5 purchases by same user on the same calendar day."""
        base_ts = datetime(2025, 1, 1, 10, 0, 0)
        
        # 5 purchases same day (no trigger)
        events_5 = [
            {"type": "purchase", "user": "alice", "timestamp": (base_ts + timedelta(hours=i)).isoformat()}
            for i in range(5)
        ]
        assert "excessive_purchases_user_day" not in check_fraud_rules(events_5)
        
        # 6 purchases same day (trigger)
        events_6 = events_5 + [
            {"type": "purchase", "user": "alice", "timestamp": (base_ts + timedelta(hours=5)).isoformat()}
        ]
        assert "excessive_purchases_user_day" in check_fraud_rules(events_6)
        
        # 6 across two days (no trigger)
        events_split = [
            {"type": "purchase", "user": "bob", "timestamp": "2025-01-01T23:00:00"},
            {"type": "purchase", "user": "bob", "timestamp": "2025-01-01T23:30:00"},
            {"type": "purchase", "user": "bob", "timestamp": "2025-01-02T00:10:00"},
            {"type": "purchase", "user": "bob", "timestamp": "2025-01-02T00:20:00"},
            {"type": "purchase", "user": "bob", "timestamp": "2025-01-02T00:30:00"},
            {"type": "purchase", "user": "bob", "timestamp": "2025-01-02T01:00:00"},
        ]
        assert "excessive_purchases_user_day" not in check_fraud_rules(events_split)

    def test_impossible_travel_scan(self):
        """Rule 4: Same ticket scanned at different locations within 30 min."""
        base_ts = datetime(2025, 1, 1, 10, 0, 0)
        
        # Same location (no trigger)
        events_same = [
            {"type": "scan", "ticket_id": "T1", "location": "London", "timestamp": base_ts.isoformat()},
            {"type": "scan", "ticket_id": "T1", "location": "London", "timestamp": (base_ts + timedelta(minutes=10)).isoformat()},
        ]
        assert "impossible_travel_scan" not in check_fraud_rules(events_same)
        
        # Different locations within 30 min (trigger)
        events_diff = [
            {"type": "scan", "ticket_id": "T2", "location": "London", "timestamp": base_ts.isoformat()},
            {"type": "scan", "ticket_id": "T2", "location": "Paris", "timestamp": (base_ts + timedelta(minutes=29)).isoformat()},
        ]
        assert "impossible_travel_scan" in check_fraud_rules(events_diff)
        
        # Different locations after 30 min (no trigger)
        events_far = [
            {"type": "scan", "ticket_id": "T3", "location": "London", "timestamp": base_ts.isoformat()},
            {"type": "scan", "ticket_id": "T3", "location": "Paris", "timestamp": (base_ts + timedelta(minutes=31)).isoformat()},
        ]
        assert "impossible_travel_scan" not in check_fraud_rules(events_far)

    def test_bulk_allocation_purchase(self):
        """Rule 5: Single purchase exceeds 20% of event capacity."""
        ts = "2025-01-01T10:00:00"
        # 19% of capacity (no trigger)
        assert "bulk_allocation_purchase" not in check_fraud_rules([{"type": "purchase", "qty": 19, "capacity": 100, "timestamp": ts}])
        
        # 20%+ (trigger)
        assert "bulk_allocation_purchase" in check_fraud_rules([{"type": "purchase", "qty": 20, "capacity": 100, "timestamp": ts}])
        assert "bulk_allocation_purchase" in check_fraud_rules([{"type": "purchase", "qty": 21, "capacity": 100, "timestamp": ts}])

    def test_coverage_edge_cases(self):
        """Hit all remaining lines and edge cases in fraud.py."""
        ts = "2025-01-01T10:00:00"
        events = [
            {"type": "other", "data": "ignored"},
            {"type": "purchase", "qty": 1, "capacity": 0, "timestamp": ts}, # capacity 0 handle
            {"type": "scan", "ticket_id": "Tunique", "timestamp": ts}, # solitary scan
        ]
        assert check_fraud_rules(events) == []


class TestSeverityMapping:
    """Unit tests for determine_severity mapping logic."""

    @pytest.mark.parametrize("rules,expected", [
        ([], "none"),
        (["duplicate_ticket_transfer"], "medium"),
        (["too_many_purchases_same_ip"], "high"),
        (["excessive_purchases_user_day"], "high"),
        (["impossible_travel_scan"], "high"),
        (["bulk_allocation_purchase"], "high"),
        (["duplicate_ticket_transfer", "too_many_purchases_same_ip"], "high"),
        (["unknown_rule"], "low"),
    ])
    def test_severity_levels(self, rules, expected):
        """Verify that severity maps correctly to the highest risk rule."""
        assert determine_severity(rules) == expected