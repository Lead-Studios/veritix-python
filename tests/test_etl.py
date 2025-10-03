from datetime import datetime, date

from src.etl import transform_summary


def test_transform_summary_empty_inputs():
    ev_rows, daily_rows = transform_summary([], [])
    assert ev_rows == []
    assert daily_rows == []


def test_transform_summary_basic_aggregation():
    events = [
        {"id": "E1", "name": "Event One"},
        {"id": "E2", "name": "Event Two"},
    ]
    sales = [
        {"event_id": "E1", "quantity": 2, "price": 10.0, "sale_date": "2025-10-01T00:00:00"},
        {"event_id": "E1", "quantity": 1, "price": 15.0, "sale_date": "2025-10-01T00:00:00"},
        {"event_id": "E2", "quantity": 3, "price": 20.0, "sale_date": "2025-10-02T00:00:00"},
    ]
    ev_rows, daily_rows = transform_summary(events, sales)
    # event summary for E1 and E2
    assert any(r["event_id"] == "E1" and r["total_tickets"] == 3 for r in ev_rows)
    assert any(r["event_id"] == "E2" and r["total_tickets"] == 3 for r in ev_rows)
    # daily rows present
    assert any(r["event_id"] == "E1" for r in daily_rows)
    assert any(r["event_id"] == "E2" for r in daily_rows)
