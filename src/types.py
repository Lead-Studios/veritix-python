from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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