"""Tests for GET /reports and GET /reports/download/{filename} endpoints.

Closes #152
"""
import os
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.main import app
from src.report_service import REPORTS_DIR

client = TestClient(app)

ADMIN_HEADERS = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

SAMPLE_REPORT_ROW = {
    "filename": "daily_report_2025-01-01_20250101_120000.csv",
    "report_date": "2025-01-01",
    "format": "csv",
    "size_bytes": 4096,
    "generated_at": "2025-01-01T12:00:00",
    "download_url": "/reports/download/daily_report_2025-01-01_20250101_120000.csv",
}


@pytest.fixture(autouse=True)
def cleanup_reports():
    yield
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.glob("daily_report_*"):
            f.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# GET /reports
# ---------------------------------------------------------------------------

class TestGetReportsList:
    def test_returns_empty_list_when_no_reports(self):
        with patch("src.report_service.list_reports", return_value=[]):
            resp = client.get("/reports", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert "reports" in body
        assert body["reports"] == []

    def test_returns_report_items(self):
        with patch("src.report_service.list_reports", return_value=[SAMPLE_REPORT_ROW]):
            resp = client.get("/reports", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["reports"]) == 1
        item = body["reports"][0]
        assert item["filename"] == SAMPLE_REPORT_ROW["filename"]
        assert item["report_date"] == SAMPLE_REPORT_ROW["report_date"]
        assert item["format"] == SAMPLE_REPORT_ROW["format"]
        assert item["size_bytes"] == SAMPLE_REPORT_ROW["size_bytes"]
        assert item["generated_at"] == SAMPLE_REPORT_ROW["generated_at"]
        assert item["download_url"] == SAMPLE_REPORT_ROW["download_url"]

    def test_returns_multiple_reports(self):
        rows = [
            {**SAMPLE_REPORT_ROW, "filename": f"daily_report_2025-01-0{i}_20250101_12000{i}.csv",
             "download_url": f"/reports/download/daily_report_2025-01-0{i}_20250101_12000{i}.csv"}
            for i in range(1, 4)
        ]
        with patch("src.report_service.list_reports", return_value=rows):
            resp = client.get("/reports", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()["reports"]) == 3

    def test_requires_admin_auth(self):
        resp = client.get("/reports")
        assert resp.status_code == 401

    def test_rejects_invalid_admin_key(self):
        resp = client.get("/reports", headers={"Authorization": "Bearer wrong_key"})
        assert resp.status_code == 403

    def test_handles_db_error_gracefully(self):
        with patch("src.report_service.list_reports", side_effect=Exception("DB down")):
            resp = client.get("/reports", headers=ADMIN_HEADERS)
        assert resp.status_code == 500
        assert "Failed to list reports" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# GET /reports/download/{filename}
# ---------------------------------------------------------------------------

class TestDownloadReport:
    def _make_report_file(self, filename: str, content: str = "col1,col2\nval1,val2\n") -> Path:
        REPORTS_DIR.mkdir(exist_ok=True)
        fp = REPORTS_DIR / filename
        fp.write_text(content)
        return fp

    def test_download_existing_csv(self):
        filename = "daily_report_2025-01-01_20250101_120000.csv"
        self._make_report_file(filename, "data")
        resp = client.get(f"/reports/download/{filename}", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    def test_download_existing_json(self):
        filename = "daily_report_2025-02-14_20250214_080000.json"
        self._make_report_file(filename, '{"report_date": "2025-02-14"}')
        resp = client.get(f"/reports/download/{filename}", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]

    def test_returns_404_for_missing_file(self):
        filename = "daily_report_2025-01-01_20250101_999999.csv"
        resp = client.get(f"/reports/download/{filename}", headers=ADMIN_HEADERS)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Report not found"

    def test_returns_400_for_invalid_filename(self):
        resp = client.get("/reports/download/../../etc/passwd", headers=ADMIN_HEADERS)
        assert resp.status_code in (400, 422)

    def test_returns_400_for_arbitrary_filename(self):
        resp = client.get("/reports/download/malicious_file.sh", headers=ADMIN_HEADERS)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid report filename"

    def test_requires_admin_auth(self):
        filename = "daily_report_2025-01-01_20250101_120000.csv"
        resp = client.get(f"/reports/download/{filename}")
        assert resp.status_code == 401

    def test_rejects_invalid_admin_key(self):
        filename = "daily_report_2025-01-01_20250101_120000.csv"
        resp = client.get(f"/reports/download/{filename}", headers={"Authorization": "Bearer bad"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# report_service unit tests
# ---------------------------------------------------------------------------

class TestCreateGeneratedReportsTable:
    def test_no_op_when_no_engine(self):
        with patch("src.report_service._pg_engine", return_value=None):
            from src.report_service import create_generated_reports_table
            # Should not raise
            create_generated_reports_table()

    def test_executes_create_table(self):
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        with patch("src.report_service._pg_engine", return_value=mock_engine):
            from src.report_service import create_generated_reports_table
            create_generated_reports_table()
        mock_conn.execute.assert_called_once()
        call_args = str(mock_conn.execute.call_args)
        assert "generated_reports" in call_args


class TestInsertReportMetadata:
    def test_no_op_when_no_engine(self):
        with patch("src.report_service._pg_engine", return_value=None):
            from src.report_service import insert_report_metadata
            insert_report_metadata("f.csv", date(2025, 1, 1), "csv", 100, datetime.utcnow())

    def test_inserts_row(self):
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        with patch("src.report_service._pg_engine", return_value=mock_engine):
            from src.report_service import insert_report_metadata
            insert_report_metadata(
                "daily_report_2025-01-01_20250101_120000.csv",
                date(2025, 1, 1),
                "csv",
                512,
                datetime(2025, 1, 1, 12, 0, 0),
            )
        mock_conn.execute.assert_called_once()


class TestListReports:
    def test_returns_empty_when_no_engine(self):
        with patch("src.report_service._pg_engine", return_value=None):
            from src.report_service import list_reports
            assert list_reports() == []

    def test_returns_formatted_rows(self):
        mock_row = (
            "daily_report_2025-01-01_20250101_120000.csv",
            date(2025, 1, 1),
            "csv",
            4096,
            datetime(2025, 1, 1, 12, 0, 0),
        )
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([mock_row]))
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_result
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        with patch("src.report_service._pg_engine", return_value=mock_engine):
            from src.report_service import list_reports
            rows = list_reports()
        assert len(rows) == 1
        assert rows[0]["filename"] == "daily_report_2025-01-01_20250101_120000.csv"
        assert rows[0]["report_date"] == "2025-01-01"
        assert rows[0]["format"] == "csv"
        assert rows[0]["size_bytes"] == 4096
        assert rows[0]["download_url"] == "/reports/download/daily_report_2025-01-01_20250101_120000.csv"


class TestScanAndPopulateReports:
    def test_no_op_when_no_engine(self):
        with patch("src.report_service._pg_engine", return_value=None):
            from src.report_service import scan_and_populate_reports
            scan_and_populate_reports()

    def test_skips_non_matching_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)
        (tmp_path / "random_file.txt").write_text("data")
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        with patch("src.report_service._pg_engine", return_value=mock_engine):
            from src.report_service import scan_and_populate_reports
            scan_and_populate_reports()
        mock_conn.execute.assert_not_called()

    def test_inserts_matching_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)
        (tmp_path / "daily_report_2025-03-15_20250315_080000.csv").write_text("data")
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        with patch("src.report_service._pg_engine", return_value=mock_engine):
            from src.report_service import scan_and_populate_reports
            scan_and_populate_reports()
        mock_conn.execute.assert_called_once()


class TestGenerateDailyReportInsertsMetadata:
    """Verify that generate_daily_report_csv calls insert_report_metadata."""

    def test_csv_inserts_metadata(self):
        sales = [{"event_id": "E1", "sale_date": "2025-06-01", "tickets_sold": 5, "revenue": 50.0}]
        with patch("src.report_service._query_daily_sales", return_value=sales), \
             patch("src.report_service._query_event_names", return_value={"E1": "Evt"}), \
             patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 0}), \
             patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 0}), \
             patch("src.report_service.insert_report_metadata") as mock_insert:
            from src.report_service import generate_daily_report_csv
            generate_daily_report_csv(target_date=date(2025, 6, 1), output_format="csv")
        mock_insert.assert_called_once()
        _, kwargs = mock_insert.call_args[0], mock_insert.call_args[1] if mock_insert.call_args[1] else {}
        args = mock_insert.call_args[0]
        assert args[2] == "csv"  # fmt

    def test_json_inserts_metadata(self):
        sales = [{"event_id": "E1", "sale_date": "2025-06-01", "tickets_sold": 5, "revenue": 50.0}]
        with patch("src.report_service._query_daily_sales", return_value=sales), \
             patch("src.report_service._query_event_names", return_value={"E1": "Evt"}), \
             patch("src.report_service._query_transfer_stats", return_value={"total_transfers": 0}), \
             patch("src.report_service._query_invalid_scans", return_value={"invalid_scans": 0}), \
             patch("src.report_service.insert_report_metadata") as mock_insert:
            from src.report_service import generate_daily_report_csv
            generate_daily_report_csv(target_date=date(2025, 6, 1), output_format="json")
        mock_insert.assert_called_once()
        args = mock_insert.call_args[0]
        assert args[2] == "json"  # fmt
