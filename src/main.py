import base64
import hmac
import io
import json
import logging
import os
import re
from datetime import date, datetime
from typing import Annotated, Any, Dict, List, Optional

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from src.auth.dependencies import require_admin_key

from src.analytics.service import analytics_service
from src.chat import ChatMessage, EscalationEvent, chat_manager
from src.config import get_settings
from src.core.ratelimit import limiter
from src.etl import diff_etl_output, extract_events_and_sales, run_etl_once, transform_summary
from src.exceptions import register_exception_handlers
from src.fraud import check_fraud_rules
from src.logging_config import (
    ETL_JOBS_TOTAL,
    FRAUD_DETECTIONS_TOTAL,
    QR_GENERATIONS_TOTAL,
    QR_VALIDATIONS_TOTAL,
    REQUEST_COUNT,
    REQUEST_DURATION,
    REQUEST_IN_PROGRESS,
    TICKET_SCANS_TOTAL,
    WEBSOCKET_CONNECTIONS,
    MetricsMiddleware,
    RequestIDMiddleware,
    get_metrics,
    get_metrics_content_type,
    log_error,
    log_info,
    log_warning,
    setup_logging,
)
from src.mock_events import get_mock_events
from src.report_service import (
    _query_daily_sales,
    _query_invalid_scans,
    _query_transfer_stats,
    create_generated_reports_table,
    generate_daily_report_csv,
    list_reports,
    scan_and_populate_reports,
)
from src.revenue_sharing_models import (
    EventRevenueInput,
    RevenueCalculationResult,
    RevenueShareConfig,
)
from src.revenue_sharing_service import revenue_sharing_service
from src.recommender import (
    build_item_similarity_matrix,
    get_item_recommendations,
    get_user_events_from_db,
)
from src.search_utils import extract_keywords, filter_events_by_keywords
from src.types_custom import (
    AnalyticsInvalidAttemptsResponse,
    AnalyticsListQuery,
    AnalyticsScansResponse,
    AnalyticsStatsQuery,
    AnalyticsTransfersResponse,
    ChatEscalateRequest,
    ChatEscalateResponse,
    ChatEscalationsResponse,
    ChatMessageHistoryQuery,
    ChatMessageHistoryResponse,
    ChatMessageSendRequest,
    ChatMessageSendResponse,
    ChatUserConversationsResponse,
    DailyReportRequest,
    DailyReportResponse,
    EventResult,
    FraudCheckRequest,
    FraudCheckResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    QRResponse,
    QRValidateRequest,
    QRValidateResponse,
    RecommendRequest,
    RecommendResponse,
    ReportItem,
    ReportsListResponse,
    RootResponse,
    SearchEventsRequest,
    SearchEventsResponse,
    TicketRequest,
)
from src.utils import compute_signature, train_logistic_regression_pipeline, validate_qr_signing_key_from_env
from src.routers.health import router as health_router

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
    from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]
    from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]
except Exception:
    BackgroundScheduler = None  # type: ignore[assignment,misc]
    CronTrigger = None  # type: ignore[assignment,misc]
    IntervalTrigger = None  # type: ignore[assignment,misc]

import uuid

app = FastAPI(
    title="Veritix Microservice",
    version="0.1.0",
    description="A microservice backend for the Veritix platform.",
)
register_exception_handlers(app)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)
app.include_router(health_router)


LOG_LEVEL: str = get_settings().LOG_LEVEL
setup_logging(LOG_LEVEL)
logger = logging.getLogger("veritix")

# Global ML pipeline — populated at startup
model_pipeline: Optional[Any] = None
# Global scheduler — populated at startup
etl_scheduler: Optional[Any] = None

# Collaborative filter mock data
mock_user_events: Dict[str, List[str]] = {
    "user1": ["concert_A", "concert_B"],
    "user2": ["concert_B", "concert_C"],
    "user3": ["concert_A", "concert_C", "concert_D"],
    "user4": ["concert_D", "concert_E"],
}


# ---------------------------------------------------------------------------
# Rate limit handler
# ---------------------------------------------------------------------------

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": "Rate limit exceeded. Try again in 60s."},
    )


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup() -> None:
    global model_pipeline, etl_scheduler
    settings = get_settings()
    create_generated_reports_table()
    if not settings.SKIP_MODEL_TRAINING:
        model_pipeline = train_logistic_regression_pipeline()

    # Ensure the generated_reports table exists and backfill from disk.
    try:
        create_generated_reports_table()
        scan_and_populate_reports()
    except Exception as exc:
        logger.warning("Report metadata init failed (non-fatal): %s", exc)

    if settings.ENABLE_ETL_SCHEDULER and BackgroundScheduler is not None:
        etl_scheduler = BackgroundScheduler(timezone="UTC")
        cron = settings.ETL_CRON
        if cron and CronTrigger is not None:
            trigger = CronTrigger.from_crontab(cron)
        else:
            minutes = settings.ETL_INTERVAL_MINUTES
            trigger = IntervalTrigger(minutes=minutes)
        etl_scheduler.add_job(run_etl_once, trigger=trigger, id="etl_job", replace_existing=True)
        etl_scheduler.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    global etl_scheduler
    log_info("Shutdown initiated: waiting for in-flight requests and scheduler...")
    if etl_scheduler is not None:
        try:
            # wait=True ensures running jobs complete before scheduler stops
            etl_scheduler.shutdown(wait=True)
            log_info("ETL scheduler shut down successfully.")
        except Exception as exc:
            log_error("Error during scheduler shutdown", {"error": str(exc)})


# ---------------------------------------------------------------------------
# Health / root / metrics
# ---------------------------------------------------------------------------

@app.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    return RootResponse(message="Veritix Service is running. Check /health for status.")

@app.get("/metrics", response_class=PlainTextResponse, response_model=str)
async def metrics_endpoint(_: str = Depends(require_admin_key)) -> PlainTextResponse:
    """Prometheus metrics endpoint (ADMIN)."""
    settings = get_settings()
    
    # Return 503 if ADMIN_API_KEY is still the default value
    if settings.ADMIN_API_KEY == "default_admin_secret_change_me":
        return PlainTextResponse(
            content="503 Service Unavailable: ADMIN_API_KEY not configured. Please set a secure ADMIN_API_KEY environment variable to access metrics.",
            status_code=503,
            media_type="text/plain"
        )
    
    log_info("Metrics endpoint requested (authenticated)")
    return PlainTextResponse(content=get_metrics(), media_type=get_metrics_content_type())


# ---------------------------------------------------------------------------
# QR endpoints
# ---------------------------------------------------------------------------

@app.post("/generate-qr", response_model=QRResponse)
def generate_qr(payload: TicketRequest) -> Any:
    log_info("QR code generation requested", {
        "ticket_id": payload.ticket_id,
        "event": payload.event,
        "user": payload.user,
    })
    unsigned: Dict[str, Any] = {
        "ticket_id": payload.ticket_id,
        "event": payload.event,
        "user": payload.user,
    }
    sig = compute_signature(unsigned)
    data: Dict[str, Any] = {**unsigned, "sig": sig}

    try:
        import qrcode as _qrcode  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]  # noqa: F401
    except Exception as exc:
        log_warning("QR generation skipped - missing dependency", {"error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "QR generation dependency missing"})

    qr = _qrcode.QRCode(
        error_correction=_qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(data, separators=(",", ":")))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    QR_GENERATIONS_TOTAL.inc()
    log_info("QR code generated successfully")
    return QRResponse(qr_base64=encoded, token=json.dumps(data, separators=(",", ":")))


@app.post("/validate-qr", response_model=QRValidateResponse)
def validate_qr(payload: QRValidateRequest) -> QRValidateResponse:
    log_info("QR validation requested")
    try:
        data: Any = json.loads(payload.qr_text)
        if not isinstance(data, dict):
            raise ValueError("QR content must be a JSON object")
        provided_sig = data.get("sig")
        if not provided_sig or not isinstance(provided_sig, str):
            raise ValueError("Missing signature")
        unsigned = {k: v for k, v in data.items() if k != "sig"}
        expected_sig = compute_signature(unsigned)
        if hmac.compare_digest(provided_sig, expected_sig):
            QR_VALIDATIONS_TOTAL.labels(result="valid").inc()
            log_info("QR validation successful", {"ticket_id": unsigned.get("ticket_id")})
            analytics_service.log_ticket_scan(
                ticket_id=str(unsigned.get("ticket_id") or "unknown"),
                event_id=str(unsigned.get("event") or "unknown"),
                is_valid=True
            )
            return QRValidateResponse(isValid=True, metadata=unsigned)
        log_warning("Invalid QR signature", {"metadata": unsigned})
        QR_VALIDATIONS_TOTAL.labels(result="invalid").inc()
        analytics_service.log_ticket_scan(
            ticket_id=str(unsigned.get("ticket_id") or "unknown"),
            event_id=str(unsigned.get("event") or "unknown"),
            is_valid=False
        )
        return QRValidateResponse(isValid=False)
    except Exception as exc:
        log_warning("Invalid QR validation attempt", {"error": str(exc)})
        QR_VALIDATIONS_TOTAL.labels(result="error").inc()
        return QRValidateResponse(isValid=False)

@app.get("/qr/scan-log/{ticket_id}")
def get_qr_scan_log(ticket_id: str) -> List[Dict[str, Any]]:
    """Returns the scan audit log for a specific ticket."""
    return analytics_service.get_scans_by_ticket_id(ticket_id)


# ---------------------------------------------------------------------------
# Analytics endpoints
# ---------------------------------------------------------------------------

@app.get("/stats", response_model=Dict[str, Any])
def get_analytics_stats(query: Annotated[AnalyticsStatsQuery, Query()]) -> Any:
    """Get analytics statistics per event or across all events."""
    event_id = query.event_id
    log_info("Analytics stats requested", {"event_id": event_id})
    try:
        if event_id:
            result = analytics_service.get_stats_for_event(event_id)
            return result
        else:
            result = analytics_service.get_stats_for_all_events()
            return result
    except Exception as exc:
        log_error("Failed to retrieve analytics stats", {"event_id": event_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics stats: {exc}")


@app.get("/stats/scans", response_model=AnalyticsScansResponse)
def get_recent_scans(query: Annotated[AnalyticsListQuery, Query()]) -> AnalyticsScansResponse:
    """Get recent scan records for an event with date filtering and pagination."""
    log_info("Recent scans requested", {
        "event_id": query.event_id,
        "from_ts": query.from_ts.isoformat() if query.from_ts else None,
        "to_ts": query.to_ts.isoformat() if query.to_ts else None,
        "page": query.page,
        "limit": query.limit
    })
    try:
        result = analytics_service.get_recent_scans(
            event_id=query.event_id,
            from_ts=query.from_ts,
            to_ts=query.to_ts,
            page=query.page,
            limit=query.limit
        )
        log_info("Recent scans retrieved", {
            "event_id": query.event_id,
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"]
        })
        return AnalyticsScansResponse(
            event_id=query.event_id,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            from_ts=query.from_ts,
            to_ts=query.to_ts
        )
    except Exception as exc:
        log_error("Failed to retrieve recent scans", {"event_id": query.event_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent scans: {exc}")


@app.get("/stats/transfers", response_model=AnalyticsTransfersResponse)
def get_recent_transfers(
    query: Annotated[AnalyticsListQuery, Query()]
) -> AnalyticsTransfersResponse:
    """Get recent transfer records for an event with date filtering and pagination."""
    log_info("Recent transfers requested", {
        "event_id": query.event_id,
        "from_ts": query.from_ts.isoformat() if query.from_ts else None,
        "to_ts": query.to_ts.isoformat() if query.to_ts else None,
        "page": query.page,
        "limit": query.limit
    })
    try:
        result = analytics_service.get_recent_transfers(
            event_id=query.event_id,
            from_ts=query.from_ts,
            to_ts=query.to_ts,
            page=query.page,
            limit=query.limit
        )
        log_info("Recent transfers retrieved", {
            "event_id": query.event_id,
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"]
        })
        return AnalyticsTransfersResponse(
            event_id=query.event_id,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            from_ts=query.from_ts,
            to_ts=query.to_ts
        )
    except Exception as exc:
        log_error("Failed to retrieve recent transfers", {"event_id": query.event_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent transfers: {exc}")


@app.get("/stats/invalid-attempts", response_model=AnalyticsInvalidAttemptsResponse)
def get_invalid_attempts(
    query: Annotated[AnalyticsListQuery, Query()]
) -> AnalyticsInvalidAttemptsResponse:
    """Get recent invalid scan attempt records for an event with date filtering and pagination."""
    log_info("Invalid attempts requested", {
        "event_id": query.event_id,
        "from_ts": query.from_ts.isoformat() if query.from_ts else None,
        "to_ts": query.to_ts.isoformat() if query.to_ts else None,
        "page": query.page,
        "limit": query.limit
    })
    try:
        result = analytics_service.get_invalid_attempts(
            event_id=query.event_id,
            from_ts=query.from_ts,
            to_ts=query.to_ts,
            page=query.page,
            limit=query.limit
        )
        log_info("Invalid attempts retrieved", {
            "event_id": query.event_id,
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"]
        })
        return AnalyticsInvalidAttemptsResponse(
            event_id=query.event_id,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            from_ts=query.from_ts,
            to_ts=query.to_ts
        )
    except Exception as exc:
        log_error("Failed to retrieve invalid attempts", {"event_id": query.event_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Failed to retrieve invalid attempts: {exc}")


# ---------------------------------------------------------------------------
# Fraud + scalper prediction
# ---------------------------------------------------------------------------

@app.post("/check-fraud", response_model=FraudCheckResponse)
def check_fraud(payload: FraudCheckRequest) -> FraudCheckResponse:
    log_info("Fraud check requested", {"event_count": len(payload.events)})
    triggered = check_fraud_rules(payload.events)
    FRAUD_DETECTIONS_TOTAL.labels(rules_triggered=str(len(triggered))).inc()
    log_info("Fraud check completed", {"triggered_rules": triggered})
    return FraudCheckResponse(triggered_rules=triggered)


@app.post("/predict-scalper", response_model=PredictResponse)
def predict_scalper(payload: PredictRequest) -> Any:
    log_info("Scalper prediction requested", {"feature_count": len(payload.features)})
    if model_pipeline is None:
        log_error("Model not ready for prediction")
        return JSONResponse(status_code=503, content={"detail": "Model not ready"})
    features = np.array(payload.features, dtype=float).reshape(1, -1)
    proba = float(model_pipeline.predict_proba(features)[0, 1])
    log_info("Scalper prediction completed", {"probability": proba})
    return PredictResponse(probability=proba)


# ---------------------------------------------------------------------------
# Search and recommendations
# ---------------------------------------------------------------------------

@app.post("/search-events", response_model=SearchEventsResponse)
def search_events(payload: SearchEventsRequest) -> Any:
    """Search for events using natural language keyword extraction."""
    try:
        keywords = extract_keywords(payload.query)
        all_events = get_mock_events()
        matching_events = filter_events_by_keywords(
            all_events,
            keywords,
            min_price=payload.min_price,
            max_price=payload.max_price,
            max_capacity=payload.max_capacity,
        )

        event_results = [
            EventResult(
                id=event["id"],
                name=event["name"],
                description=event["description"],
                event_type=event["event_type"],
                location=event["location"],
                date=event["date"],
                price=event["price"],
                capacity=event["capacity"],
            )
            for event in matching_events
        ]

        return SearchEventsResponse(
            query=payload.query,
            results=event_results,
            count=len(event_results),
            keywords_extracted=keywords,
        )
    except Exception as exc:
        logger.error("Search events failed: %s", exc)
        return JSONResponse(status_code=500, content={"detail": f"Search failed: {exc}"})


@app.post("/recommend-events", response_model=RecommendResponse)
def recommend_events(payload: RecommendRequest) -> RecommendResponse:
    user_id = payload.user_id
    # Prefer DB-sourced history; fall back to mock data when DB is unavailable.
    user_events_dict = get_user_events_from_db()
    if not user_events_dict:
        user_events_dict = mock_user_events
    similarity_matrix = build_item_similarity_matrix(user_events_dict)
    recommended = get_item_recommendations(
        user_id=user_id,
        user_events_dict=user_events_dict,
        similarity_matrix=similarity_matrix,
        top_n=3,
    )
    return RecommendResponse(recommendations=recommended)


# ---------------------------------------------------------------------------
# Revenue sharing
# ---------------------------------------------------------------------------

@app.post("/calculate-revenue-share", response_model=RevenueCalculationResult)
def calculate_revenue_share(input_data: EventRevenueInput) -> RevenueCalculationResult:
    """Calculate revenue shares for stakeholders based on event sales."""
    log_info("Revenue share calculation requested", {
        "event_id": input_data.event_id,
        "total_sales": input_data.total_sales,
        "ticket_count": input_data.ticket_count,
    })
    is_valid, errors = revenue_sharing_service.validate_input(input_data)
    if not is_valid:
        log_error("Revenue share validation failed", {"errors": errors})
        raise HTTPException(status_code=400, detail={"errors": errors})
    try:
        result = revenue_sharing_service.calculate_revenue_shares(input_data)
        return result
    except Exception as exc:
        log_error("Revenue share calculation failed", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Revenue calculation failed: {exc}")


@app.post("/calculate-revenue-share/batch", response_model=List[RevenueCalculationResult])
def calculate_revenue_share_batch(
    inputs: List[EventRevenueInput],
) -> List[RevenueCalculationResult]:
    """Calculate revenue shares for multiple events."""
    log_info("Batch revenue share calculation requested", {"event_count": len(inputs)})
    results: List[RevenueCalculationResult] = []
    for input_data in inputs:
        try:
            is_valid, errors = revenue_sharing_service.validate_input(input_data)
            if not is_valid:
                continue
            results.append(revenue_sharing_service.calculate_revenue_shares(input_data))
        except Exception as exc:
            log_error("Batch revenue calculation failed", {
                "event_id": input_data.event_id,
                "error": str(exc),
            })
    log_info("Batch calculation completed", {
        "processed_count": len(results),
        "requested_count": len(inputs),
    })
    return results


@app.get("/revenue-share/config", response_model=RevenueShareConfig)
def get_revenue_share_config() -> RevenueShareConfig:
    """Return the current revenue sharing configuration."""
    log_info("Revenue share configuration requested")
    return revenue_sharing_service.config


@app.get("/revenue-share/example", response_model=EventRevenueInput)
def get_example_revenue_input() -> EventRevenueInput:
    """Return an example revenue calculation input."""
    log_info("Revenue share example input requested")
    return EventRevenueInput(
        event_id="event_123",
        total_sales=10000.0,
        ticket_count=100,
        currency="USD",
        additional_fees={"service_fee": 50.0},
    )


# ---------------------------------------------------------------------------
# Daily report
# ---------------------------------------------------------------------------

@app.post("/generate-daily-report", response_model=DailyReportResponse)
def generate_daily_report(payload: DailyReportRequest) -> Any:
    try:
        target_date: date = payload.target_date or date.today()
        settings = get_settings()
        report_path, cache_hit = generate_daily_report_csv(
            target_date=target_date,
            output_format=payload.output_format,
            event_id=payload.event_id,
            force_regenerate=payload.force_regenerate,
            cache_minutes=settings.REPORT_CACHE_MINUTES,
        )
        sales_data = _query_daily_sales(target_date)
        transfer_stats = _query_transfer_stats(target_date)
        invalid_scan_stats = _query_invalid_scans(target_date)

        total_sales: int = sum(row["tickets_sold"] for row in sales_data)
        total_revenue: float = sum(row["revenue"] for row in sales_data)

        msg = "Report served from cache" if cache_hit else f"Report generated successfully at {report_path}"
        return DailyReportResponse(
            success=True,
            report_path=report_path,
            report_date=str(target_date),
            summary={
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "total_transfers": transfer_stats.get("total_transfers", 0),
                "invalid_scans": invalid_scan_stats.get("invalid_scans", 0),
            },
            cache_hit=cache_hit,
            message=msg,
        )
    except Exception as exc:
        log_error("Daily report generation failed", {"error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": f"Report generation failed: {exc}"})


@app.get("/reports", response_model=ReportsListResponse)
def get_reports_list(
    _: str = Depends(require_admin_key),
) -> ReportsListResponse:
    """List up to 100 most recently generated reports (ADMIN)."""
    log_info("Reports list requested")
    try:
        rows = list_reports()
        items = [ReportItem(**row) for row in rows]
        return ReportsListResponse(reports=items)
    except Exception as exc:
        log_error("Failed to list reports", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {exc}")


# Safe filename pattern — must match what generate_daily_report_csv produces
_SAFE_REPORT_FILENAME = re.compile(r"^daily_report_\d{4}-\d{2}-\d{2}_\d{8}_\d{6}\.(csv|json)$")


@app.get("/reports/download/{filename}")
def download_report(
    filename: str,
    _: str = Depends(require_admin_key),
) -> FileResponse:
    """Stream a previously generated report file (ADMIN)."""
    if not _SAFE_REPORT_FILENAME.match(filename):
        raise HTTPException(status_code=400, detail="Invalid report filename")

    from src.report_service import REPORTS_DIR
    filepath = REPORTS_DIR / filename
    # Resolve to an absolute path and confirm it stays inside REPORTS_DIR
    try:
        resolved = filepath.resolve()
        reports_resolved = REPORTS_DIR.resolve()
        resolved.relative_to(reports_resolved)
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid report filename")

    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Report not found")

    media_type = "application/json" if filename.endswith(".json") else "text/csv"
    log_info("Report download requested", {"filename": filename})
    return FileResponse(path=str(resolved), media_type=media_type, filename=filename)


# ---------------------------------------------------------------------------
# Chat — HTTP endpoints
# ---------------------------------------------------------------------------

@app.websocket("/ws/chat/{conversation_id}/{user_id}")
async def websocket_chat(
    websocket: WebSocket, conversation_id: str, user_id: str
) -> None:
    """WebSocket endpoint for real-time chat."""
    await chat_manager.connect(websocket, conversation_id, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data: Dict[str, Any] = json.loads(data)
                message = ChatMessage(
                    id=str(uuid.uuid4()),
                    sender_id=user_id,
                    sender_type=message_data.get("sender_type", "user"),
                    content=message_data["content"],
                    timestamp=datetime.utcnow(),
                    conversation_id=conversation_id,
                    metadata=message_data.get("metadata", {}),
                )
                await chat_manager.send_message(message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from client")
            except KeyError as exc:
                logger.warning("Missing required field: %s", exc)
            except Exception as exc:
                logger.error("Error processing message: %s", exc)
    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected for user %s in conversation %s",
            user_id,
            conversation_id,
        )
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
    finally:
        await chat_manager.disconnect(websocket, conversation_id, user_id)


@app.post("/chat/{conversation_id}/messages", response_model=ChatMessageSendResponse)
async def send_message(
    conversation_id: str, message: ChatMessageSendRequest
) -> ChatMessageSendResponse:
    """Send a chat message via HTTP."""
    try:
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            sender_id=message.sender_id,
            sender_type=message.sender_type,
            content=message.content,
            timestamp=datetime.utcnow(),
            conversation_id=conversation_id,
            metadata=message.metadata,
        )
        success = await chat_manager.send_message(chat_message)
        if success:
            return ChatMessageSendResponse(status="success", message_id=chat_message.id)
        raise HTTPException(status_code=500, detail="Failed to send message")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error sending message: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to send message")


@app.get("/chat/{conversation_id}/history", response_model=ChatMessageHistoryResponse)
async def get_message_history(
    conversation_id: str,
    query: Annotated[ChatMessageHistoryQuery, Query()],
) -> ChatMessageHistoryResponse:
    """Get message history for a conversation."""
    try:
        messages = chat_manager.get_message_history(conversation_id, query.limit)
        return ChatMessageHistoryResponse(
            conversation_id=conversation_id,
            messages=[msg.model_dump() for msg in messages],
            count=len(messages),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error getting message history: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to get message history")


@app.post("/chat/{conversation_id}/escalate", response_model=ChatEscalateResponse)
async def escalate_conversation(
    conversation_id: str, escalation: ChatEscalateRequest
) -> ChatEscalateResponse:
    """Escalate a conversation to human support."""
    try:
        escalation_event: EscalationEvent = await chat_manager.escalate_conversation(
            conversation_id, escalation.reason, escalation.metadata
        )
        return ChatEscalateResponse(
            status="success",
            escalation_id=escalation_event.id,
            reason=escalation_event.reason,
            timestamp=escalation_event.timestamp.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error escalating conversation: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to escalate conversation")


@app.get("/chat/{conversation_id}/escalations", response_model=ChatEscalationsResponse)
async def get_escalations(conversation_id: str) -> ChatEscalationsResponse:
    """Get escalation events for a conversation."""
    try:
        escalations = chat_manager.get_escalations(conversation_id)
        return ChatEscalationsResponse(
            conversation_id=conversation_id,
            escalations=[esc.model_dump() for esc in escalations],
            count=len(escalations),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error getting escalations: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to get escalations")


@app.get("/chat/user/{user_id}/conversations", response_model=ChatUserConversationsResponse)
async def get_user_conversations(user_id: str) -> ChatUserConversationsResponse:
    """Get all conversations for a user."""
    try:
        conversation_ids = chat_manager.get_user_conversations(user_id)
        return ChatUserConversationsResponse(
            user_id=user_id,
            conversations=conversation_ids,
            count=len(conversation_ids),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error getting user conversations: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to get user conversations")


# ---------------------------------------------------------------------------
# Trending events
# ---------------------------------------------------------------------------

@app.get("/events/trending", response_model=List[Dict[str, Any]])
def get_trending_events(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of trending events to return"),
) -> Any:
    """Return top events ranked by ticket scan velocity in the last 24 hours.

    Results are cached for 10 minutes.
    """
    try:
        results = analytics_service.get_trending_events(limit=limit, hours=24)
        return results
    except Exception as exc:
        log_error("Failed to get trending events", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Failed to get trending events: {exc}")


# ---------------------------------------------------------------------------
# ETL diff (dry-run) — admin only
# ---------------------------------------------------------------------------

# In-memory store for async ETL diff jobs
_etl_diff_jobs: Dict[str, Any] = {}


@app.get("/etl/diff")
def etl_diff(request: Request) -> Any:
    """Dry-run ETL diff: show what the next ETL run would load without committing.

    Requires X-Admin-Key header matching ADMIN_API_KEY.
    For slow extracts (> 5 s) returns HTTP 202 with a job_id for async polling.
    """
    import threading
    import time as _time

    api_key = request.headers.get("X-Admin-Key", "")
    if api_key != get_settings().ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")

    start = _time.monotonic()
    try:
        events, sales = extract_events_and_sales()
        elapsed = _time.monotonic() - start

        ev_rows, daily_rows = transform_summary(
            [e.raw for e in events], [s.raw for s in sales]
        )

        if elapsed > 5.0:
            job_id = str(uuid.uuid4())

            def _run_diff() -> None:
                result = diff_etl_output(ev_rows, daily_rows)
                _etl_diff_jobs[job_id] = {"status": "complete", "result": result}

            _etl_diff_jobs[job_id] = {"status": "pending"}
            threading.Thread(target=_run_diff, daemon=True).start()
            return JSONResponse(
                status_code=202,
                content={"job_id": job_id, "status": "pending"},
            )

        result = diff_etl_output(ev_rows, daily_rows)
        return result

    except HTTPException:
        raise
    except Exception as exc:
        log_error("ETL diff failed", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=f"ETL diff failed: {exc}")