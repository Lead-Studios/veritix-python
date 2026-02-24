import json
import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from src.config import get_settings

# Ensure required settings exist for import-time configuration.
os.environ.setdefault("QR_SIGNING_KEY", "x" * 32)
os.environ.setdefault("DATABASE_URL", "sqlite:///./stdlib-tests.db")
os.environ.setdefault("NEST_API_BASE_URL", "https://nest.example.test")
get_settings.cache_clear()

from src.chat import ChatManager, ChatMessage
from src.etl import transform_summary
from src.fraud import check_fraud_rules, determine_severity
from src.manager import TicketScanManager
from src.mock_events import get_mock_events
from src.report_service import generate_daily_report_csv
from src.revenue_sharing_models import EventRevenueInput
from src.revenue_sharing_service import RevenueSharingService
from src.search_utils import extract_keywords, filter_events_by_keywords
from src.signer import _b64u_decode, _b64u_encode
from src.utils import compute_signature


class _DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent_text = []
        self.sent_json = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, value):
        self.sent_text.append(value)

    async def send_json(self, value):
        self.sent_json.append(value)


class TestConfigModule(unittest.TestCase):
    def test_get_settings_is_cached(self):
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        self.assertIs(s1, s2)


class TestUtilsModule(unittest.TestCase):
    def test_compute_signature_is_stable(self):
        payload = {"a": 1, "b": "x"}
        sig1 = compute_signature(payload)
        sig2 = compute_signature(payload)
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)


class TestFraudModule(unittest.TestCase):
    def test_check_fraud_rules_and_severity(self):
        now = datetime.utcnow().replace(microsecond=0)
        events = [
            {"type": "purchase", "ip": "1.1.1.1", "user": "u1", "ticket_id": "t1", "timestamp": now.isoformat()},
            {"type": "purchase", "ip": "1.1.1.1", "user": "u1", "ticket_id": "t2", "timestamp": now.isoformat()},
            {"type": "purchase", "ip": "1.1.1.1", "user": "u1", "ticket_id": "t3", "timestamp": now.isoformat()},
            {"type": "purchase", "ip": "1.1.1.1", "user": "u1", "ticket_id": "t4", "timestamp": now.isoformat()},
            {"type": "transfer", "ticket_id": "t9", "timestamp": now.isoformat()},
            {"type": "transfer", "ticket_id": "t9", "timestamp": now.isoformat()},
        ]
        triggered = check_fraud_rules(events)
        self.assertIn("too_many_purchases_same_ip", triggered)
        self.assertIn("duplicate_ticket_transfer", triggered)
        self.assertEqual(determine_severity(triggered), "high")


class TestSearchModule(unittest.TestCase):
    def test_extract_keywords_and_filter(self):
        keywords = extract_keywords("music events in lagos this weekend")
        self.assertIn("music", keywords["event_types"])
        self.assertIn("Lagos", keywords["locations"])
        events = get_mock_events()
        filtered = filter_events_by_keywords(events, keywords)
        self.assertTrue(len(filtered) > 0)
        for event in filtered:
            self.assertIn("lagos", event["location"].lower())


class TestEtlModule(unittest.TestCase):
    def test_transform_summary(self):
        events = [{"id": "E1", "name": "Event One"}]
        sales = [{"event_id": "E1", "quantity": 2, "price": 10.0, "sale_date": "2025-10-01T00:00:00"}]
        ev_rows, daily_rows = transform_summary(events, sales)
        self.assertEqual(len(ev_rows), 1)
        self.assertEqual(ev_rows[0]["event_id"], "E1")
        self.assertEqual(ev_rows[0]["total_tickets"], 2)
        self.assertEqual(len(daily_rows), 1)
        self.assertEqual(daily_rows[0]["tickets_sold"], 2)


class TestManagerModule(unittest.IsolatedAsyncioTestCase):
    async def test_connect_broadcast_disconnect(self):
        manager = TicketScanManager(session_timeout_minutes=30)
        ws = _DummyWebSocket()

        await manager.connect(ws)
        self.assertTrue(ws.accepted)
        self.assertEqual(len(manager.active_connections), 1)

        await manager.broadcast_scan({"ticket_id": "T1"})
        self.assertEqual(len(ws.sent_json), 1)

        await manager.disconnect(ws)
        self.assertEqual(len(manager.active_connections), 0)


class TestChatModule(unittest.IsolatedAsyncioTestCase):
    async def test_send_and_history(self):
        manager = ChatManager()
        ws = _DummyWebSocket()
        await manager.connect(ws, "c1", "u1")

        msg = ChatMessage(
            id="m1",
            sender_id="u1",
            sender_type="user",
            content="hello",
            timestamp=datetime.utcnow(),
            conversation_id="c1",
            metadata={},
        )
        ok = await manager.send_message(msg)
        self.assertTrue(ok)
        history = manager.get_message_history("c1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].content, "hello")

        await manager.disconnect(ws, "c1", "u1")


class TestRevenueSharingModule(unittest.TestCase):
    def test_calculate_revenue_shares(self):
        service = RevenueSharingService()
        payload = EventRevenueInput(
            event_id="evt_1",
            total_sales=1000.0,
            ticket_count=100,
            currency="USD",
        )
        result = service.calculate_revenue_shares(payload)
        self.assertEqual(result.event_id, "evt_1")
        self.assertTrue(result.net_revenue > 0)
        self.assertTrue(len(result.distributions) > 0)


class TestReportServiceModule(unittest.TestCase):
    def test_generate_daily_report_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.report_service.REPORTS_DIR", new=Path(tmpdir)):
                with patch("src.report_service._query_daily_sales", return_value=[{"event_id": "E1", "sale_date": "2025-10-04", "tickets_sold": 5, "revenue": 100.0}]):
                    with patch("src.report_service._query_event_names", return_value={"E1": "Show"}):
                        with patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 1}):
                            with patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 0}):
                                path = generate_daily_report_csv(target_date=date(2025, 10, 4), output_format="json")
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["summary"]["total_sales"], 5)
            self.assertEqual(data["sales_by_event"][0]["event_name"], "Show")


class TestSignerModule(unittest.TestCase):
    def test_base64_helpers_roundtrip(self):
        original = b"abc123+/="
        encoded = _b64u_encode(original)
        decoded = _b64u_decode(encoded)
        self.assertEqual(original, decoded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
