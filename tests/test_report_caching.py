"""Tests for report generation caching (issue #156).

Covers:
- Cache hit: returns existing file without regenerating
- Cache miss: generates a fresh file when no cached entry exists
- force_regenerate: bypasses cache and always writes a new file
- Endpoint-level: cache_hit flag surfaces in the API response
"""
import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.report_service import (
    REPORTS_DIR,
    check_report_cache,
    generate_daily_report_csv,
    insert_report_metadata,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_SALES = [
    {"event_id": "E1", "sale_date": "2025-01-01", "tickets_sold": 10, "revenue": 100.0}
]
_MOCK_NAMES = {"E1": "Test Event"}
_MOCK_TRANSFERS = {"total_transfers": 0}
_MOCK_SCANS = {"invalid_scans": 0}

_DB_PATCHES = [
    ("src.report_service._query_daily_sales", _MOCK_SALES),
    ("src.report_service._query_event_names", _MOCK_NAMES),
    ("src.report_service._query_transfer_stats", _MOCK_TRANSFERS),
    ("src.report_service._query_invalid_scans", _MOCK_SCANS),
]


def _patch_db(func):
    """Decorator: patches all four DB query helpers."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        patches = [patch(target, return_value=value) for target, value in _DB_PATCHES]
        for p in patches:
            p.start()
        try:
            return func(*args, **kwargs)
        finally:
            for p in patches:
                p.stop()

    return wrapper


@pytest.fixture(autouse=True)
def cleanup_reports():
    yield
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.glob("daily_report_*"):
            f.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Unit tests: generate_daily_report_csv
# ---------------------------------------------------------------------------


class TestCacheMiss:
    @_patch_db
    def test_returns_path_and_false_on_no_db(self, tmp_path, monkeypatch):
        """With no DB engine, cache is always missed and file is generated."""
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)
        with patch("src.report_service._pg_engine", return_value=None):
            path, cache_hit = generate_daily_report_csv(
                target_date=date(2025, 1, 1), output_format="csv"
            )
        assert not cache_hit
        assert Path(path).exists()
        assert "daily_report_2025-01-01" in path

    @_patch_db
    def test_inserts_metadata_after_generation(self, tmp_path, monkeypatch):
        """insert_report_metadata is called once after a fresh CSV is written."""
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)
        with patch("src.report_service._pg_engine", return_value=None), \
             patch("src.report_service.insert_report_metadata") as mock_insert:
            path, cache_hit = generate_daily_report_csv(
                target_date=date(2025, 1, 1), output_format="csv"
            )
        mock_insert.assert_called_once()
        call_kwargs = mock_insert.call_args
        assert call_kwargs.kwargs["fmt"] == "csv"
        assert not cache_hit

    @_patch_db
    def test_cache_miss_json(self, tmp_path, monkeypatch):
        """Cache miss for JSON format generates a .json file."""
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)
        with patch("src.report_service._pg_engine", return_value=None):
            path, cache_hit = generate_daily_report_csv(
                target_date=date(2025, 1, 1), output_format="json"
            )
        assert not cache_hit
        assert path.endswith(".json")


class TestCacheHit:
    @_patch_db
    def test_returns_existing_file_without_rewriting(self, tmp_path, monkeypatch):
        """When check_report_cache returns metadata and the file exists, no new file is written."""
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)

        # Pre-create the "cached" file
        cached_filename = "daily_report_2025-01-01_cached.csv"
        cached_file = tmp_path / cached_filename
        cached_file.write_text("cached content")

        cached_meta = {
            "filename": cached_filename,
            "size_bytes": cached_file.stat().st_size,
            "generated_at": datetime(2025, 1, 1, 10, 0, 0),
        }

        with patch("src.report_service.check_report_cache", return_value=cached_meta) as mock_check, \
             patch("src.report_service.insert_report_metadata") as mock_insert:
            path, cache_hit = generate_daily_report_csv(
                target_date=date(2025, 1, 1),
                output_format="csv",
                cache_minutes=60,
            )

        assert cache_hit is True
        assert path == str(tmp_path / cached_filename)
        mock_check.assert_called_once_with(date(2025, 1, 1), None, "csv", 60)
        # No new metadata row should be inserted for a cache hit
        mock_insert.assert_not_called()

    @_patch_db
    def test_cache_hit_skipped_when_file_missing(self, tmp_path, monkeypatch):
        """If DB says cached but file is gone, fall through and regenerate."""
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)

        cached_meta = {
            "filename": "daily_report_2025-01-01_gone.csv",
            "size_bytes": 512,
            "generated_at": datetime(2025, 1, 1, 10, 0, 0),
        }

        with patch("src.report_service.check_report_cache", return_value=cached_meta), \
             patch("src.report_service._pg_engine", return_value=None):
            path, cache_hit = generate_daily_report_csv(
                target_date=date(2025, 1, 1),
                output_format="csv",
                cache_minutes=60,
            )

        assert not cache_hit
        assert Path(path).exists()


class TestForceRegenerate:
    @_patch_db
    def test_force_regenerate_skips_cache_check(self, tmp_path, monkeypatch):
        """force_regenerate=True does not call check_report_cache."""
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)

        with patch("src.report_service.check_report_cache") as mock_check, \
             patch("src.report_service._pg_engine", return_value=None):
            path, cache_hit = generate_daily_report_csv(
                target_date=date(2025, 1, 1),
                output_format="csv",
                force_regenerate=True,
            )

        mock_check.assert_not_called()
        assert not cache_hit
        assert Path(path).exists()

    @_patch_db
    def test_force_regenerate_writes_new_file_even_when_cached(self, tmp_path, monkeypatch):
        """force_regenerate=True always produces a new file even if cache would hit."""
        monkeypatch.setattr("src.report_service.REPORTS_DIR", tmp_path)

        # check_report_cache would normally hit, but it should never be called
        cached_meta = {
            "filename": "daily_report_2025-01-01_old.csv",
            "size_bytes": 10,
            "generated_at": datetime(2025, 1, 1, 10, 0, 0),
        }

        with patch("src.report_service.check_report_cache", return_value=cached_meta) as mock_check, \
             patch("src.report_service._pg_engine", return_value=None):
            path, cache_hit = generate_daily_report_csv(
                target_date=date(2025, 1, 1),
                output_format="csv",
                force_regenerate=True,
            )

        mock_check.assert_not_called()
        assert not cache_hit


# ---------------------------------------------------------------------------
# Unit tests: check_report_cache
# ---------------------------------------------------------------------------


class TestCheckReportCache:
    def test_returns_none_when_no_engine(self):
        with patch("src.report_service._pg_engine", return_value=None):
            result = check_report_cache(date(2025, 1, 1), None, "csv", 60)
        assert result is None

    def test_returns_none_when_no_rows(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn

        with patch("src.report_service._pg_engine", return_value=mock_engine):
            result = check_report_cache(date(2025, 1, 1), None, "csv", 60)
        assert result is None

    def test_returns_metadata_dict_when_row_exists(self):
        fake_row = ("daily_report_2025-01-01_abc.csv", 4096, datetime(2025, 1, 1, 9, 0))
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchone.return_value = fake_row
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn

        with patch("src.report_service._pg_engine", return_value=mock_engine):
            result = check_report_cache(date(2025, 1, 1), None, "csv", 60)

        assert result is not None
        assert result["filename"] == "daily_report_2025-01-01_abc.csv"
        assert result["size_bytes"] == 4096


# ---------------------------------------------------------------------------
# Unit tests: insert_report_metadata
# ---------------------------------------------------------------------------


class TestInsertReportMetadata:
    def test_no_op_when_no_engine(self):
        with patch("src.report_service._pg_engine", return_value=None):
            # Should not raise
            insert_report_metadata(
                filename="test.csv",
                report_date=date(2025, 1, 1),
                event_id=None,
                fmt="csv",
                size_bytes=1024,
                generated_at=datetime(2025, 1, 1),
            )

    def test_executes_insert(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn

        with patch("src.report_service._pg_engine", return_value=mock_engine):
            insert_report_metadata(
                filename="daily_report_2025-01-01_x.csv",
                report_date=date(2025, 1, 1),
                event_id="E1",
                fmt="csv",
                size_bytes=2048,
                generated_at=datetime(2025, 1, 1, 12, 0),
            )

        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestEndpointCacheHit:
    def test_cache_hit_flag_in_response(self):
        """When generate_daily_report_csv returns cache_hit=True, API reflects it."""
        with patch(
            "src.main.generate_daily_report_csv",
            return_value=("reports/daily_report_2025-01-01_x.csv", True),
        ), patch("src.main._query_daily_sales", return_value=_MOCK_SALES), \
           patch("src.main._query_transfer_stats", return_value=_MOCK_TRANSFERS), \
           patch("src.main._query_invalid_scans", return_value=_MOCK_SCANS):
            response = client.post(
                "/generate-daily-report",
                json={"target_date": "2025-01-01", "output_format": "csv"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cache_hit"] is True
        assert "cache" in data["message"].lower()

    def test_cache_miss_flag_in_response(self):
        """When generate_daily_report_csv returns cache_hit=False, API reflects it."""
        with patch(
            "src.main.generate_daily_report_csv",
            return_value=("reports/daily_report_2025-01-01_new.csv", False),
        ), patch("src.main._query_daily_sales", return_value=_MOCK_SALES), \
           patch("src.main._query_transfer_stats", return_value=_MOCK_TRANSFERS), \
           patch("src.main._query_invalid_scans", return_value=_MOCK_SCANS):
            response = client.post(
                "/generate-daily-report",
                json={"target_date": "2025-01-01", "output_format": "csv"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit"] is False
        assert "generated" in data["message"].lower()


class TestEndpointForceRegenerate:
    def test_force_regenerate_passes_flag_to_service(self):
        """force_regenerate=true is forwarded to generate_daily_report_csv."""
        with patch(
            "src.main.generate_daily_report_csv",
            return_value=("reports/daily_report_2025-01-01_fresh.csv", False),
        ) as mock_gen, \
             patch("src.main._query_daily_sales", return_value=_MOCK_SALES), \
             patch("src.main._query_transfer_stats", return_value=_MOCK_TRANSFERS), \
             patch("src.main._query_invalid_scans", return_value=_MOCK_SCANS):
            response = client.post(
                "/generate-daily-report",
                json={
                    "target_date": "2025-01-01",
                    "output_format": "csv",
                    "force_regenerate": True,
                },
            )

        assert response.status_code == 200
        _, call_kwargs = mock_gen.call_args
        assert call_kwargs["force_regenerate"] is True

    def test_force_regenerate_default_is_false(self):
        """force_regenerate defaults to False when not supplied."""
        with patch(
            "src.main.generate_daily_report_csv",
            return_value=("reports/daily_report_2025-01-01_x.csv", False),
        ) as mock_gen, \
             patch("src.main._query_daily_sales", return_value=_MOCK_SALES), \
             patch("src.main._query_transfer_stats", return_value=_MOCK_TRANSFERS), \
             patch("src.main._query_invalid_scans", return_value=_MOCK_SCANS):
            client.post(
                "/generate-daily-report",
                json={"target_date": "2025-01-01"},
            )

        _, call_kwargs = mock_gen.call_args
        assert call_kwargs["force_regenerate"] is False


class TestEndpointCacheMinutes:
    def test_report_cache_minutes_from_settings(self):
        """REPORT_CACHE_MINUTES from settings is forwarded to the service."""
        with patch(
            "src.main.generate_daily_report_csv",
            return_value=("reports/daily_report_2025-01-01_x.csv", False),
        ) as mock_gen, \
             patch("src.main._query_daily_sales", return_value=_MOCK_SALES), \
             patch("src.main._query_transfer_stats", return_value=_MOCK_TRANSFERS), \
             patch("src.main._query_invalid_scans", return_value=_MOCK_SCANS), \
             patch("src.main.get_settings") as mock_settings:
            mock_settings.return_value.REPORT_CACHE_MINUTES = 30
            mock_settings.return_value.SKIP_MODEL_TRAINING = True
            mock_settings.return_value.ENABLE_ETL_SCHEDULER = False
            client.post("/generate-daily-report", json={"target_date": "2025-01-01"})

        _, call_kwargs = mock_gen.call_args
        assert call_kwargs["cache_minutes"] == 30
