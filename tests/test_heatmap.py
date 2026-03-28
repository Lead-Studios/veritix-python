"""Tests for GET /stats/heatmap — hourly scan density per event."""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.analytics.service import AnalyticsService
from src.config import settings
from src.main import app

client = TestClient(app)

SERVICE_HEADERS = {"Authorization": f"Bearer {settings.SERVICE_API_KEY}"}


# ---------------------------------------------------------------------------
# Service-layer unit tests
# ---------------------------------------------------------------------------


class TestGetScanHeatmap:
    def setup_method(self):
        self.service = AnalyticsService()

    def _make_row(self, hour: int, count: int):
        row = MagicMock()
        row.hour = hour
        row.scan_count = count
        return row

    def _mock_session(self, rows):
        """Return a patched get_session whose query chain yields *rows*."""
        mock_session = MagicMock()
        (
            mock_session.query.return_value
            .filter.return_value
            .group_by.return_value
            .all.return_value
        ) = rows
        # Chained .filter().filter().group_by().all() for date-scoped queries
        (
            mock_session.query.return_value
            .filter.return_value
            .filter.return_value
            .group_by.return_value
            .all.return_value
        ) = rows
        return mock_session

    def test_returns_24_entries_always(self):
        """Response data must contain exactly 24 hourly entries."""
        rows = [self._make_row(14, 320), self._make_row(15, 400)]
        mock_session = self._mock_session(rows)

        with patch("src.analytics.service.get_session", return_value=mock_session):
            result = self.service.get_scan_heatmap("event-abc")

        assert len(result["data"]) == 24

    def test_zero_fill_missing_hours(self):
        """Hours with no scans must appear with scan_count == 0."""
        rows = [self._make_row(10, 50)]
        mock_session = self._mock_session(rows)

        with patch("src.analytics.service.get_session", return_value=mock_session):
            result = self.service.get_scan_heatmap("event-abc")

        data = {entry["hour"]: entry["scan_count"] for entry in result["data"]}
        assert data[10] == 50
        # All other hours should be 0
        for h in range(24):
            if h != 10:
                assert data[h] == 0, f"hour {h} should be 0, got {data[h]}"

    def test_correct_hour_bucketing(self):
        """Scan counts must be placed in the correct hour bucket."""
        rows = [
            self._make_row(0, 5),
            self._make_row(8, 100),
            self._make_row(23, 77),
        ]
        mock_session = self._mock_session(rows)

        with patch("src.analytics.service.get_session", return_value=mock_session):
            result = self.service.get_scan_heatmap("event-abc")

        data = {entry["hour"]: entry["scan_count"] for entry in result["data"]}
        assert data[0] == 5
        assert data[8] == 100
        assert data[23] == 77

    def test_peak_hour_is_highest_count_hour(self):
        """peak_hour must point to the hour with the maximum scan count."""
        rows = [
            self._make_row(14, 300),
            self._make_row(15, 500),
            self._make_row(16, 200),
        ]
        mock_session = self._mock_session(rows)

        with patch("src.analytics.service.get_session", return_value=mock_session):
            result = self.service.get_scan_heatmap("event-abc")

        assert result["peak_hour"] == 15

    def test_peak_hour_defaults_to_zero_when_no_scans(self):
        """When there are no scans, peak_hour should be 0 (first of all-zero hours)."""
        mock_session = self._mock_session([])

        with patch("src.analytics.service.get_session", return_value=mock_session):
            result = self.service.get_scan_heatmap("event-abc")

        assert result["peak_hour"] == 0
        assert all(entry["scan_count"] == 0 for entry in result["data"])

    def test_event_id_propagated(self):
        """event_id in the result must match the one passed in."""
        mock_session = self._mock_session([])

        with patch("src.analytics.service.get_session", return_value=mock_session):
            result = self.service.get_scan_heatmap("event-xyz-123")

        assert result["event_id"] == "event-xyz-123"

    def test_date_filter_applied(self):
        """When filter_date is given the query chain uses the extra .filter() call."""
        rows = [self._make_row(9, 42)]
        mock_session = MagicMock()

        # We need to capture what query path is exercised.
        (
            mock_session.query.return_value
            .filter.return_value
            .filter.return_value
            .group_by.return_value
            .all.return_value
        ) = rows

        with patch("src.analytics.service.get_session", return_value=mock_session):
            result = self.service.get_scan_heatmap("event-abc", filter_date=date(2026, 3, 28))

        # Verify the second .filter() was called (date scoping)
        mock_session.query.return_value.filter.return_value.filter.assert_called_once()
        assert result["data"][9]["scan_count"] == 42

    def test_session_always_closed(self):
        """Session must be closed even when an exception is raised."""
        mock_session = MagicMock()
        mock_session.query.side_effect = RuntimeError("db exploded")

        with patch("src.analytics.service.get_session", return_value=mock_session):
            with pytest.raises(RuntimeError):
                self.service.get_scan_heatmap("event-abc")

        mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestHeatmapEndpoint:
    """Tests for GET /stats/heatmap via TestClient."""

    _sample_result = {
        "event_id": "event-001",
        "data": [{"hour": h, "scan_count": 10 if h == 14 else 0} for h in range(24)],
        "peak_hour": 14,
    }

    def test_missing_auth_returns_401(self):
        response = client.get("/stats/heatmap", params={"event_id": "event-001"})
        assert response.status_code == 401

    def test_invalid_token_returns_403(self):
        headers = {"Authorization": "Bearer completely_wrong_token"}
        response = client.get(
            "/stats/heatmap",
            params={"event_id": "event-001"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_missing_event_id_returns_422(self):
        response = client.get("/stats/heatmap", headers=SERVICE_HEADERS)
        assert response.status_code == 422

    def test_valid_request_returns_200(self):
        with patch(
            "src.main.analytics_service.get_scan_heatmap",
            return_value=self._sample_result,
        ):
            response = client.get(
                "/stats/heatmap",
                params={"event_id": "event-001"},
                headers=SERVICE_HEADERS,
            )

        assert response.status_code == 200

    def test_response_shape(self):
        with patch(
            "src.main.analytics_service.get_scan_heatmap",
            return_value=self._sample_result,
        ):
            response = client.get(
                "/stats/heatmap",
                params={"event_id": "event-001"},
                headers=SERVICE_HEADERS,
            )

        body = response.json()
        assert body["event_id"] == "event-001"
        assert body["peak_hour"] == 14
        assert len(body["data"]) == 24

    def test_all_24_hours_present_in_response(self):
        with patch(
            "src.main.analytics_service.get_scan_heatmap",
            return_value=self._sample_result,
        ):
            response = client.get(
                "/stats/heatmap",
                params={"event_id": "event-001"},
                headers=SERVICE_HEADERS,
            )

        hours = [entry["hour"] for entry in response.json()["data"]]
        assert hours == list(range(24))

    def test_date_param_forwarded_to_service(self):
        captured = {}

        def fake_heatmap(event_id, filter_date=None):
            captured["filter_date"] = filter_date
            return {
                "event_id": event_id,
                "data": [{"hour": h, "scan_count": 0} for h in range(24)],
                "peak_hour": 0,
            }

        with patch("src.main.analytics_service.get_scan_heatmap", side_effect=fake_heatmap):
            response = client.get(
                "/stats/heatmap",
                params={"event_id": "event-001", "date": "2026-03-28"},
                headers=SERVICE_HEADERS,
            )

        assert response.status_code == 200
        assert captured["filter_date"] == date(2026, 3, 28)

    def test_service_error_returns_500(self):
        with patch(
            "src.main.analytics_service.get_scan_heatmap",
            side_effect=RuntimeError("db failure"),
        ):
            response = client.get(
                "/stats/heatmap",
                params={"event_id": "event-001"},
                headers=SERVICE_HEADERS,
            )

        assert response.status_code == 500
        assert "Failed to retrieve scan heatmap" in response.json()["detail"]

    def test_peak_hour_accuracy(self):
        """peak_hour in the response must match the hour with the max scan_count."""
        data = [{"hour": h, "scan_count": 0} for h in range(24)]
        data[17]["scan_count"] = 999
        result = {"event_id": "event-001", "data": data, "peak_hour": 17}

        with patch("src.main.analytics_service.get_scan_heatmap", return_value=result):
            response = client.get(
                "/stats/heatmap",
                params={"event_id": "event-001"},
                headers=SERVICE_HEADERS,
            )

        assert response.json()["peak_hour"] == 17
        assert response.json()["data"][17]["scan_count"] == 999
