"""Persist fraud check results to a fraud_events table for audit trail and trend analysis."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import src.db as _db

Base = declarative_base()


class FraudEvent(Base):
    """ORM model for a persisted fraud check result."""

    __tablename__ = "fraud_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    triggered_rules = Column(Text, nullable=False)   # JSON list of rule names
    severity = Column(String(20), nullable=False)
    event_id = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_fraud_events_severity", "severity"),
    )


def get_session():
    engine = _db.get_engine()
    if engine is None:
        raise RuntimeError("Database engine is not initialised")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def save_fraud_result(
    triggered_rules: List[str],
    severity: str,
    event_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist a fraud check result and return the saved record as a dict."""
    session = get_session()
    try:
        record = FraudEvent(
            triggered_rules=json.dumps(triggered_rules),
            severity=severity,
            event_id=event_id,
            notes=notes,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return {
            "id": record.id,
            "checked_at": record.checked_at.isoformat(),
            "triggered_rules": triggered_rules,
            "severity": record.severity,
            "event_id": record.event_id,
        }
    finally:
        session.close()


def get_fraud_events(
    event_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Retrieve persisted fraud events, optionally filtered by event_id or severity."""
    session = get_session()
    try:
        query = session.query(FraudEvent).order_by(FraudEvent.checked_at.desc())
        if event_id:
            query = query.filter(FraudEvent.event_id == event_id)
        if severity:
            query = query.filter(FraudEvent.severity == severity)
        records = query.limit(limit).all()
        return [
            {
                "id": r.id,
                "checked_at": r.checked_at.isoformat(),
                "triggered_rules": json.loads(r.triggered_rules),
                "severity": r.severity,
                "event_id": r.event_id,
            }
            for r in records
        ]
    finally:
        session.close()
