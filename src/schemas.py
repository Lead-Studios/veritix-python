# app/schemas.py
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class TicketScan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str
    event_id: str
    scanner_id: Optional[str] = None
    timestamp: datetime
    meta: Optional[Dict[str, Any]] = Field(default=None)
