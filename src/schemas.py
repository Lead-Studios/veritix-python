# app/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketScan(BaseModel):
    ticket_id: str
    event_id: str
    scanner_id: Optional[str] = None
    timestamp: datetime
    meta: Optional[dict] = None
