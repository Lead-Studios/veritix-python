from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Fraud Detection Types ---
class FraudCheckRequest(BaseModel):
    """Request body for /check-fraud endpoint.
    Contains a list of ticket purchase and transfer events to check for suspicious activity.
    """
    events: List[Dict[str, Any]] = Field(
        ..., description="List of event dicts. Each event should include at least: type (purchase|transfer), user, ip, ticket_id, timestamp (ISO8601 string)."
    )

class FraudCheckResponse(BaseModel):
    triggered_rules: List[str] = Field(
        ..., description="List of fraud rule names triggered by the submitted events."
    )

class PredictRequest(BaseModel):
    """Request body for /predict-scalper endpoint.

    Each record represents aggregated event signals for a buyer/session.
    """
    features: List[float] = Field(
        ..., description="Feature vector: e.g., [tickets_per_txn, txns_per_min, avg_price_ratio, account_age_days, zip_mismatch, device_changes]"
    )


class PredictResponse(BaseModel):
    probability: float


class TicketRequest(BaseModel):
    ticket_id: str = Field(..., pattern=r"^[A-Za-z0-9_-]+$", description="Alphanumeric ticket identifier")
    event: str = Field(..., min_length=1, description="Event name")
    user: str = Field(..., min_length=1, description="User identifier or email")


class QRResponse(BaseModel):
    qr_base64: str


class QRValidateRequest(BaseModel):
    qr_text: str = Field(..., description="Decoded text content from the QR code (JSON)")


class QRValidateResponse(BaseModel):
    isValid: bool
    metadata: Optional[Dict[str, Any]] = None
