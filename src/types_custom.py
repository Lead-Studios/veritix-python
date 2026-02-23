from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# --- Fraud Detection Types ---
class FraudCheckRequest(BaseModel):
    """Request body for /check-fraud endpoint.
    Contains a list of ticket purchase and transfer events to check for suspicious activity.
    """
    model_config = ConfigDict(extra="forbid")
    events: List[Dict[str, Any]] = Field(
        ..., description="List of event dicts. Each event should include at least: type (purchase|transfer), user, ip, ticket_id, timestamp (ISO8601 string)."
    )

class FraudCheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    triggered_rules: List[str] = Field(
        ..., description="List of fraud rule names triggered by the submitted events."
    )

class PredictRequest(BaseModel):
    """Request body for /predict-scalper endpoint.

    Each record represents aggregated event signals for a buyer/session.
    """
    model_config = ConfigDict(extra="forbid")
    features: List[float] = Field(
        ..., description="Feature vector: e.g., [tickets_per_txn, txns_per_min, avg_price_ratio, account_age_days, zip_mismatch, device_changes]"
    )

    @field_validator("features")
    @classmethod
    def validate_feature_length(cls, value: List[float]) -> List[float]:
        if len(value) != 6:
            raise ValueError("features must contain exactly 6 values")
        return value


class PredictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    probability: float


class TicketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str = Field(..., pattern=r"^[A-Za-z0-9_-]+$", description="Alphanumeric ticket identifier")
    event: str = Field(..., min_length=1, description="Event name")
    user: str = Field(..., min_length=1, description="User identifier or email")


class QRResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qr_base64: str


class QRValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qr_text: str = Field(..., description="Decoded text content from the QR code (JSON)")


class QRValidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    isValid: bool
    metadata: Optional[Dict[str, Any]] = None


# --- Search Events Types ---
class SearchEventsRequest(BaseModel):
    """Request body for /search-events endpoint.
    
    Contains a natural language query to search for events.
    """
    model_config = ConfigDict(extra="forbid")
    query: str = Field(
        ..., 
        min_length=1, 
        description="Natural language search query (e.g., 'music events in Lagos this weekend')"
    )


class EventResult(BaseModel):
    """Represents a single event in search results."""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="Unique event identifier")
    name: str = Field(..., description="Event name")
    description: str = Field(..., description="Event description")
    event_type: str = Field(..., description="Event category/type")
    location: str = Field(..., description="Event location")
    date: str = Field(..., description="Event date in ISO format")
    price: float = Field(..., description="Ticket price")
    capacity: int = Field(..., description="Venue capacity")


class SearchEventsResponse(BaseModel):
    """Response body for /search-events endpoint."""
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., description="The original search query")
    results: List[EventResult] = Field(..., description="List of matching events")
    count: int = Field(..., description="Number of results found")
    keywords_extracted: Dict[str, Any] = Field(..., description="Keywords extracted from the query")


class DailyReportRequest(BaseModel):
    """Request body for /generate-daily-report endpoint."""
    model_config = ConfigDict(extra="forbid")
    target_date: Optional[date] = Field(None, description="Target date in YYYY-MM-DD format. Defaults to today.")
    output_format: Literal["csv", "json"] = Field("csv", description="Output format: 'csv' or 'json'")


class DailyReportResponse(BaseModel):
    """Response body for /generate-daily-report endpoint."""
    model_config = ConfigDict(extra="forbid")
    success: bool = Field(..., description="Whether report generation succeeded")
    report_path: Optional[str] = Field(None, description="Path to generated report file")
    report_date: str = Field(..., description="Date of the report")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    message: Optional[str] = Field(None, description="Additional information or error message")


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(..., min_length=1)


class RecommendResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendations: List[str]


class ChatMessageSendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sender_id: str = Field(..., min_length=1)
    sender_type: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatMessageSendResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["success"]
    message_id: str


class ChatMessageItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    sender_id: str
    sender_type: str
    content: str
    timestamp: datetime
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageHistoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(50, ge=1, le=500)


class ChatMessageHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: str
    messages: List[ChatMessageItem]
    count: int


class ChatEscalateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field("user_request", min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatEscalateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["success"]
    escalation_id: str
    reason: str
    timestamp: str


class EscalationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    conversation_id: str
    reason: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatEscalationsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: str
    escalations: List[EscalationItem]
    count: int


class ChatUserConversationsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    conversations: List[str]
    count: int


class AnalyticsStatsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: Optional[str] = None


class AnalyticsListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(..., min_length=1)
    limit: int = Field(50, ge=1, le=500)


class AnalyticsScansResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    scans: List[Dict[str, Any]]
    count: int


class AnalyticsTransfersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    transfers: List[Dict[str, Any]]
    count: int


class AnalyticsInvalidAttemptsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    attempts: List[Dict[str, Any]]
    count: int


class RootResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    service: str
    api_version: str
