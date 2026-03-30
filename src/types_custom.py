from datetime import date as dt_date, datetime
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

    @field_validator("events")
    @classmethod
    def validate_event_count(cls, value: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(value) > 1000:
            raise ValueError("events must contain at most 1000 items")
        return value

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
        if len(value) > 100:
            raise ValueError("features must contain at most 100 values")
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
    token: str


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

    Contains a natural language query to search for events and optional
    price/capacity filters that override NLP-inferred values.
    """
    model_config = ConfigDict(extra="forbid")
    query: str = Field(
        ...,
        min_length=1,
        description="Natural language search query (e.g., 'music events in Lagos this weekend')",
    )
    min_price: Optional[float] = Field(
        None, ge=0, description="Minimum ticket price filter (inclusive)"
    )
    max_price: Optional[float] = Field(
        None, ge=0, description="Maximum ticket price filter (inclusive)"
    )
    max_capacity: Optional[int] = Field(
        None, ge=1, description="Maximum venue capacity filter (inclusive)"
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
    target_date: Optional[dt_date] = Field(None, description="Target date in YYYY-MM-DD format. Defaults to today.")
    output_format: Literal["csv", "json"] = Field("csv", description="Output format: 'csv' or 'json'")
    event_id: Optional[str] = Field(None, description="Optional event ID to scope the report. Null means all events.")
    force_regenerate: bool = Field(False, description="When True, skip cache and always generate a fresh report.")


class DailyReportResponse(BaseModel):
    """Response body for /generate-daily-report endpoint."""
    model_config = ConfigDict(extra="forbid")
    success: bool = Field(..., description="Whether report generation succeeded")
    report_path: Optional[str] = Field(None, description="Path to generated report file")
    report_date: str = Field(..., description="Date of the report")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    cache_hit: bool = Field(False, description="True when the response was served from a cached report")
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


class ChatTypingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sender_id: str = Field(..., min_length=1)
    is_typing: bool


class ChatTypingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["success"]


class ChatAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_id: str = Field(..., min_length=1)


class ChatAssignResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["success"]
    conversation_id: str
    agent_id: str


class ChatQueueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: str
    escalated_at: datetime
    reason: str


class ChatQueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    queue: List[ChatQueueItem]
    count: int


class ChatConversationStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: str
    status: Literal["open", "escalated", "assigned", "resolved"]
    assigned_agent_id: Optional[str] = None


class AnalyticsStatsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: Optional[str] = None


class AnalyticsListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(..., min_length=1)
    from_ts: Optional[datetime] = Field(None, description="Start datetime filter (ISO string)")
    to_ts: Optional[datetime] = Field(None, description="End datetime filter (ISO string)")
    page: int = Field(1, ge=1, description="Page number (1-based)")
    limit: int = Field(100, ge=1, le=1000, description="Items per page (max 1000)")


class AnalyticsScansResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    data: List[Dict[str, Any]] = Field(..., description="Paginated scan records")
    total: int = Field(..., description="Total number of records matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    limit: int = Field(..., description="Items per page")
    from_ts: Optional[datetime] = Field(None, description="Start datetime filter applied")
    to_ts: Optional[datetime] = Field(None, description="End datetime filter applied")


class AnalyticsTransfersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    data: List[Dict[str, Any]] = Field(..., description="Paginated transfer records")
    total: int = Field(..., description="Total number of records matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    limit: int = Field(..., description="Items per page")
    from_ts: Optional[datetime] = Field(None, description="Start datetime filter applied")
    to_ts: Optional[datetime] = Field(None, description="End datetime filter applied")


class AnalyticsInvalidAttemptsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    data: List[Dict[str, Any]] = Field(..., description="Paginated invalid attempt records")
    total: int = Field(..., description="Total number of records matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    limit: int = Field(..., description="Items per page")
    from_ts: Optional[datetime] = Field(None, description="Start datetime filter applied")
    to_ts: Optional[datetime] = Field(None, description="End datetime filter applied")


class HeatmapEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    scan_count: int = Field(..., ge=0, description="Number of scans in this hour")


class HeatmapQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(..., min_length=1, description="Event UUID to scope the heatmap")
    date: Optional[dt_date] = Field(None, description="Optional ISO date (YYYY-MM-DD) to scope to a specific day")


class HeatmapResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    data: List[HeatmapEntry] = Field(..., description="24-entry array of hourly scan counts (hours 0-23)")
    peak_hour: int = Field(..., ge=0, le=23, description="Hour with the highest scan count")


class RootResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    service: str
    api_version: str


class ReportItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(..., description="Report filename")
    report_date: str = Field(..., description="Date the report covers (YYYY-MM-DD)")
    format: str = Field(..., description="File format: csv or json")
    size_bytes: int = Field(..., description="File size in bytes")
    generated_at: str = Field(..., description="ISO timestamp when the report was generated")
    download_url: str = Field(..., description="Relative URL to download the report")


class ReportsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reports: List[ReportItem] = Field(..., description="List of generated reports (up to 100)")
