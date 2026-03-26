"""Tests for issue #162: ETL validate_rows() step."""
from datetime import date, datetime, timedelta, timezone

from src.etl import validate_rows


def _future_date(days_ahead: int = 2) -> date:
    return datetime.now(tz=timezone.utc).date() + timedelta(days=days_ahead)


def _past_date(days_ago: int = 1) -> date:
    return datetime.now(tz=timezone.utc).date() - timedelta(days=days_ago)


# ---------------------------------------------------------------------------
# Valid rows pass through unchanged
# ---------------------------------------------------------------------------

def test_valid_rows_pass_through():
    ev_rows = [{"event_id": "E1", "total_tickets": 10, "total_revenue": 100.0}]
    daily_rows = [{"event_id": "E1", "sale_date": _past_date()}]

    valid_ev, valid_daily, rejected = validate_rows(ev_rows, daily_rows)

    assert valid_ev == ev_rows
    assert valid_daily == daily_rows
    assert rejected == 0


# ---------------------------------------------------------------------------
# event_summary rows — rejections
# ---------------------------------------------------------------------------

def test_rejects_event_row_with_empty_event_id():
    ev_rows = [{"event_id": "", "total_tickets": 5, "total_revenue": 50.0}]
    valid_ev, _, rejected = validate_rows(ev_rows, [])
    assert valid_ev == []
    assert rejected == 1


def test_rejects_event_row_with_none_event_id():
    ev_rows = [{"event_id": None, "total_tickets": 5, "total_revenue": 50.0}]
    valid_ev, _, rejected = validate_rows(ev_rows, [])
    assert valid_ev == []
    assert rejected == 1


def test_rejects_event_row_with_negative_total_tickets():
    ev_rows = [{"event_id": "E2", "total_tickets": -1, "total_revenue": 50.0}]
    valid_ev, _, rejected = validate_rows(ev_rows, [])
    assert valid_ev == []
    assert rejected == 1


def test_rejects_event_row_with_negative_total_revenue():
    ev_rows = [{"event_id": "E3", "total_tickets": 5, "total_revenue": -0.01}]
    valid_ev, _, rejected = validate_rows(ev_rows, [])
    assert valid_ev == []
    assert rejected == 1


def test_accepts_event_row_with_zero_tickets_and_revenue():
    """Zero is valid — only negative values are rejected."""
    ev_rows = [{"event_id": "E4", "total_tickets": 0, "total_revenue": 0.0}]
    valid_ev, _, rejected = validate_rows(ev_rows, [])
    assert len(valid_ev) == 1
    assert rejected == 0


# ---------------------------------------------------------------------------
# daily_rows — rejections
# ---------------------------------------------------------------------------

def test_rejects_daily_row_with_empty_event_id():
    daily_rows = [{"event_id": "", "sale_date": _past_date()}]
    _, valid_daily, rejected = validate_rows([], daily_rows)
    assert valid_daily == []
    assert rejected == 1


def test_rejects_daily_row_with_future_sale_date():
    daily_rows = [{"event_id": "E5", "sale_date": _future_date(days_ahead=2)}]
    _, valid_daily, rejected = validate_rows([], daily_rows)
    assert valid_daily == []
    assert rejected == 1


def test_accepts_daily_row_with_today_sale_date():
    """A sale_date of today (0 days ahead) is within the 1-day tolerance."""
    today = datetime.now(tz=timezone.utc).date()
    daily_rows = [{"event_id": "E6", "sale_date": today}]
    _, valid_daily, rejected = validate_rows([], daily_rows)
    assert len(valid_daily) == 1
    assert rejected == 0


def test_accepts_daily_row_with_tomorrow_sale_date():
    """A sale_date of tomorrow (1 day ahead) is at the boundary — accepted."""
    tomorrow = datetime.now(tz=timezone.utc).date() + timedelta(days=1)
    daily_rows = [{"event_id": "E7", "sale_date": tomorrow}]
    _, valid_daily, rejected = validate_rows([], daily_rows)
    assert len(valid_daily) == 1
    assert rejected == 0


def test_accepts_daily_row_with_past_sale_date():
    daily_rows = [{"event_id": "E8", "sale_date": _past_date()}]
    _, valid_daily, rejected = validate_rows([], daily_rows)
    assert len(valid_daily) == 1
    assert rejected == 0


def test_daily_row_sale_date_as_iso_string():
    """sale_date passed as ISO string is parsed and validated correctly."""
    past_iso = (_past_date()).isoformat()
    daily_rows = [{"event_id": "E9", "sale_date": past_iso}]
    _, valid_daily, rejected = validate_rows([], daily_rows)
    assert len(valid_daily) == 1
    assert rejected == 0


def test_daily_row_future_date_as_iso_string_rejected():
    future_iso = (_future_date(days_ahead=3)).isoformat()
    daily_rows = [{"event_id": "E10", "sale_date": future_iso}]
    _, valid_daily, rejected = validate_rows([], daily_rows)
    assert valid_daily == []
    assert rejected == 1


# ---------------------------------------------------------------------------
# Mixed batches
# ---------------------------------------------------------------------------

def test_mixed_batch_correct_rejected_count():
    ev_rows = [
        {"event_id": "E1", "total_tickets": 10, "total_revenue": 100.0},  # valid
        {"event_id": "", "total_tickets": 5, "total_revenue": 50.0},       # invalid
        {"event_id": "E3", "total_tickets": -2, "total_revenue": 20.0},   # invalid
    ]
    daily_rows = [
        {"event_id": "E1", "sale_date": _past_date()},                     # valid
        {"event_id": "E1", "sale_date": _future_date(days_ahead=5)},      # invalid
    ]
    valid_ev, valid_daily, rejected = validate_rows(ev_rows, daily_rows)

    assert len(valid_ev) == 1
    assert valid_ev[0]["event_id"] == "E1"
    assert len(valid_daily) == 1
    assert rejected == 3


def test_empty_inputs_return_zero_rejected():
    valid_ev, valid_daily, rejected = validate_rows([], [])
    assert valid_ev == []
    assert valid_daily == []
    assert rejected == 0
