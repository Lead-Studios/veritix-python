import httpx
import pytest
from sqlalchemy import text
from src.etl import run_etl_once
from src.config import get_settings

def _response(status_code: int, url: str, payload):
    request = httpx.Request("GET", url)
    return httpx.Response(status_code=status_code, json=payload, request=request)

class DummyClient:
    def __init__(self, side_effects_map):
        self._side_effects_map = side_effects_map
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers or {}, "params": params})
        # Extract base path for matching (e.g., /events or /ticket-sales)
        for path, effects in self._side_effects_map.items():
            if path in url:
                if not effects:
                    raise ValueError(f"No mock responses left for path: {path}")
                effect = effects.pop(0)
                if isinstance(effect, Exception):
                    raise effect
                return effect
        raise ValueError(f"No mock for URL: {url}")

@pytest.mark.integration
def test_full_etl_pipeline_integration(monkeypatch, db_engine, clean_test_db):
    """
    Integration test for the full ETL pipeline.
    
    1. Mocks NestJS API to return 3 events and 10 sales records.
    2. Runs run_etl_once().
    3. Verifies data in PostgreSQL (event_sales_summary, daily_ticket_sales).
    4. Runs again with updated sales to test upsert logic.
    5. Verifies log entry in etl_run_log.
    """
    # 1. Setup mocks for first run (3 events, 10 sales)
    events_data = [
        {"id": "E1", "name": "Event 1"},
        {"id": "E2", "name": "Event 2"},
        {"id": "E3", "name": "Event 3"},
    ]
    # 10 sales records spread across 3 events and 2 dates
    sales_data = [
        {"event_id": "E1", "qty": 2, "price": 50.0, "sale_date": "2024-01-01T10:00:00"},
        {"event_id": "E1", "qty": 1, "price": 50.0, "sale_date": "2024-01-01T11:00:00"},
        {"event_id": "E1", "qty": 1, "price": 50.0, "sale_date": "2024-01-02T10:00:00"},
        {"event_id": "E2", "qty": 5, "price": 20.0, "sale_date": "2024-01-01T10:00:00"},
        {"event_id": "E2", "qty": 1, "price": 20.0, "sale_date": "2024-01-01T11:00:00"},
        {"event_id": "E3", "qty": 1, "price": 100.0, "sale_date": "2024-01-01T10:00:00"},
        {"event_id": "E3", "qty": 1, "price": 100.0, "sale_date": "2024-01-01T11:00:00"},
        {"event_id": "E3", "qty": 1, "price": 100.0, "sale_date": "2024-01-01T12:00:00"},
        {"event_id": "E3", "qty": 1, "price": 100.0, "sale_date": "2024-01-01T13:00:00"},
        {"event_id": "E3", "qty": 1, "price": 100.0, "sale_date": "2024-01-02T10:00:00"},
    ]

    side_effects = {
        "/events": [_response(200, "/events", {"data": events_data})],
        "/ticket-sales": [_response(200, "/ticket-sales", {"data": sales_data})],
    }
    
    dummy_client = DummyClient(side_effects)
    monkeypatch.setattr("src.etl.extract.httpx.Client", lambda timeout: dummy_client)
    
    # 2. Run ETL
    run_etl_once()
    
    # 3. Assertions for Run 1
    with db_engine.connect() as conn:
        # event_sales_summary should have 3 rows
        rows = conn.execute(text("SELECT event_id, total_tickets, total_revenue FROM event_sales_summary ORDER BY event_id")).fetchall()
        assert len(rows) == 3
        
        # E1: 3 sales totalling 4 tickets, 200 rev
        assert rows[0][0] == "E1"
        assert int(rows[0][1]) == 4
        assert float(rows[0][2]) == 200.0
        
        # E2: 2 sales totalling 6 tickets, 120 rev
        assert rows[1][0] == "E2"
        assert int(rows[1][1]) == 6
        assert float(rows[1][2]) == 120.0
        
        # E3: 5 sales totalling 5 tickets, 500 rev
        assert rows[2][0] == "E3"
        assert int(rows[2][1]) == 5
        assert float(rows[2][2]) == 500.0

        # daily_ticket_sales breakdown
        # E1 on 2024-01-01: 3 tickets (2+1), 150 rev
        row_e1_d1 = conn.execute(text("SELECT tickets_sold, revenue FROM daily_ticket_sales WHERE event_id='E1' AND sale_date='2024-01-01'")).fetchone()
        assert int(row_e1_d1[0]) == 3
        assert float(row_e1_d1[1]) == 150.0

    # 4. Run again with updated sales data for upsert test
    # E1 gets 2 more sales on 2024-01-01 (adding 2 qty)
    # Important: In this implementation, transform_summary aggregates everything provided in 'sales'.
    # If the API returns the same records again, they will be summed again.
    # The requirement says "updated sales data", so we simulate a second run where more data is returned.
    new_sale = {"event_id": "E1", "qty": 2, "price": 50.0, "sale_date": "2024-01-01T15:00:00"}
    updated_sales_data = sales_data + [new_sale]
    
    side_effects["/events"].append(_response(200, "/events", {"data": events_data}))
    side_effects["/ticket-sales"].append(_response(200, "/ticket-sales", {"data": updated_sales_data}))
    
    run_etl_once()
    
    # 5. Assertions for Run 2 (Upsert)
    with db_engine.connect() as conn:
        # E1: 4 (old) + 2 (new) = 6 tickets, 200 + 100 = 300 rev
        row_e1 = conn.execute(text("SELECT total_tickets, total_revenue FROM event_sales_summary WHERE event_id='E1'")).fetchone()
        assert int(row_e1[0]) == 6
        assert float(row_e1[1]) == 300.0
        
        # E1 daily on 2024-01-01: 3 (old) + 2 (new) = 5 tickets, 150 + 100 = 250 rev
        row_e1_d1_new = conn.execute(text("SELECT tickets_sold, revenue FROM daily_ticket_sales WHERE event_id='E1' AND sale_date='2024-01-01'")).fetchone()
        assert int(row_e1_d1_new[0]) == 5
        assert float(row_e1_d1_new[1]) == 250.0
        
        # etl_run_log should have 2 entries, status="success"
        log_rows = conn.execute(text("SELECT status FROM etl_run_log")).fetchall()
        assert len(log_rows) == 2
        assert all(r[0] == "success" for r in log_rows)
