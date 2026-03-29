import logging
from typing import List, Optional
from sqlalchemy import text
from src.db import get_engine
from src.revenue_sharing_models import Stakeholder

logger = logging.getLogger("veritix.stakeholder_store")

def create_stakeholders_table() -> None:
    """Create the stakeholders table if it does not yet exist."""
    engine = get_engine()
    if engine is None:
        logger.info("Skiaging stakeholder table creation — no DB engine")
        return
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stakeholders (
                id              TEXT PRIMARY KEY,
                event_id        TEXT NOT NULL,
                name            TEXT NOT NULL,
                role            TEXT NOT NULL,
                percentage      FLOAT NOT NULL,
                fixed_amount    FLOAT,
                min_amount      FLOAT,
                max_amount      FLOAT,
                payment_address TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    logger.info("stakeholders table ready")

def get_stakeholders_for_event(event_id: str) -> List[Stakeholder]:
    """Retrieve stakeholders for a specific event from the database."""
    engine = get_engine()
    if engine is None:
        return []
    
    query = text("""
        SELECT id, name, role, percentage, fixed_amount, min_amount, max_amount, payment_address
        FROM stakeholders
        WHERE event_id = :event_id
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"event_id": event_id})
        stakeholders = []
        for row in result:
            stakeholders.append(Stakeholder(
                id=row[0],
                name=row[1],
                role=row[2],
                percentage=row[3],
                fixed_amount=row[4],
                min_amount=row[5],
                max_amount=row[6],
                payment_address=row[7]
            ))
        return stakeholders

def save_stakeholders_for_event(event_id: str, stakeholders: List[Stakeholder]) -> None:
    """Save (upsert) stakeholders for a specific event to the database."""
    engine = get_engine()
    if engine is None:
        return
    
    with engine.connect() as conn:
        # We'll use a transaction to delete existing stakeholders and insert new ones
        # or we could use an upsert. For simplicity and correctness with the requirement
        # of "saving custom stakeholder config", we'll replace existing ones.
        
        # Delete existing ones for this event
        conn.execute(text("DELETE FROM stakeholders WHERE event_id = :event_id"), {"event_id": event_id})
        
        # Insert new ones
        if stakeholders:
            insert_query = text("""
                INSERT INTO stakeholders (id, event_id, name, role, percentage, fixed_amount, min_amount, max_amount, payment_address)
                VALUES (:id, :event_id, :name, :role, :percentage, :fixed_amount, :min_amount, :max_amount, :payment_address)
            """)
            
            for s in stakeholders:
                conn.execute(insert_query, {
                    "id": s.id,
                    "event_id": event_id,
                    "name": s.name,
                    "role": s.role,
                    "percentage": s.percentage,
                    "fixed_amount": s.fixed_amount,
                    "min_amount": s.min_amount,
                    "max_amount": s.max_amount,
                    "payment_address": s.payment_address
                })
        
        conn.commit()
    logger.info(f"Saved {len(stakeholders)} stakeholders for event {event_id}")
