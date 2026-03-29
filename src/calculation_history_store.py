import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from src.db import get_engine
from src.revenue_sharing_models import RevenueCalculationResult, PayoutDistribution

logger = logging.getLogger("veritix.calculation_history_store")

def create_revenue_calculations_table() -> None:
    """Create the revenue_calculations table if it does not yet exist."""
    engine = get_engine()
    if engine is None:
        logger.info("Skipping revenue_calculations table creation — no DB engine")
        return
    
    with engine.connect() as conn:
        # Use FLOAT and TEXT for cross-DB compatibility (SQLite/Postgres)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS revenue_calculations (
                id                  TEXT PRIMARY KEY,
                event_id            TEXT NOT NULL,
                total_gross_sales   FLOAT NOT NULL,
                total_fees          FLOAT NOT NULL,
                net_revenue         FLOAT NOT NULL,
                distributions       TEXT NOT NULL,
                total_paid_out      FLOAT NOT NULL,
                remaining_balance   FLOAT NOT NULL,
                rules_applied       TEXT NOT NULL,
                calculated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    logger.info("revenue_calculations table ready")

def save_calculation(result: RevenueCalculationResult) -> str:
    """Persist a revenue calculation result to the database."""
    engine = get_engine()
    if engine is None:
        return ""
    
    calculation_id = str(uuid.uuid4())
    
    query = text("""
        INSERT INTO revenue_calculations (
            id, event_id, total_gross_sales, total_fees, net_revenue, 
            distributions, total_paid_out, remaining_balance, rules_applied
        ) VALUES (
            :id, :event_id, :total_gross_sales, :total_fees, :net_revenue, 
            :distributions, :total_paid_out, :remaining_balance, :rules_applied
        )
    """)
    
    with engine.connect() as conn:
        conn.execute(query, {
            "id": calculation_id,
            "event_id": result.event_id,
            "total_gross_sales": result.total_gross_sales,
            "total_fees": result.total_fees,
            "net_revenue": result.net_revenue,
            "distributions": json.dumps([d.model_dump() for d in result.distributions]),
            "total_paid_out": result.total_paid_out,
            "remaining_balance": result.remaining_balance,
            "rules_applied": json.dumps(result.rules_applied)
        })
        conn.commit()
    
    logger.info(f"Saved revenue calculation {calculation_id} for event {result.event_id}")
    return calculation_id

def get_history_for_event(event_id: str, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve paginated calculation history for an event."""
    engine = get_engine()
    if engine is None:
        return []
    
    offset = (page - 1) * limit
    
    query = text("""
        SELECT id, event_id, total_gross_sales, total_fees, net_revenue, 
               distributions, total_paid_out, remaining_balance, rules_applied, calculated_at
        FROM revenue_calculations
        WHERE event_id = :event_id
        ORDER BY calculated_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"event_id": event_id, "limit": limit, "offset": offset})
        history = []
        for row in result:
            history.append(_row_to_dict(row))
        return history

def get_calculation_by_id(calculation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific calculation by its ID."""
    engine = get_engine()
    if engine is None:
        return None
    
    query = text("""
        SELECT id, event_id, total_gross_sales, total_fees, net_revenue, 
               distributions, total_paid_out, remaining_balance, rules_applied, calculated_at
        FROM revenue_calculations
        WHERE id = :id
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"id": calculation_id}).fetchone()
        if result:
            return _row_to_dict(result)
        return None

def _row_to_dict(row) -> Dict[str, Any]:
    """Helper to convert a DB row to a dictionary with parsed JSON fields."""
    return {
        "id": row[0],
        "event_id": row[1],
        "total_gross_sales": row[2],
        "total_fees": row[3],
        "net_revenue": row[4],
        "distributions": json.loads(row[5]),
        "total_paid_out": row[6],
        "remaining_balance": row[7],
        "rules_applied": json.loads(row[8]),
        "calculated_at": row[9]
    }
