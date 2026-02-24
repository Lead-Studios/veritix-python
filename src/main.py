
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel, Field
from typing import List
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from typing import Dict, List

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import base64
import io
import json
import hmac
import logging
from typing import Any

from src.utils import compute_signature, train_logistic_regression_pipeline
from src.etl import run_etl_once
from src.chat import chat_manager, ChatMessage, EscalationEvent
from src.logging_config import (
    setup_logging, RequestIDMiddleware, MetricsMiddleware,
    get_metrics, get_metrics_content_type,
    REQUEST_COUNT, REQUEST_DURATION, REQUEST_IN_PROGRESS,
    WEBSOCKET_CONNECTIONS, CHAT_MESSAGES_TOTAL, ETL_JOBS_TOTAL,
    TICKET_SCANS_TOTAL, FRAUD_DETECTIONS_TOTAL,
    QR_GENERATIONS_TOTAL, QR_VALIDATIONS_TOTAL,
    log_info, log_error, log_warning
)

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
except Exception:
    BackgroundScheduler = None
    CronTrigger = None
    IntervalTrigger = None
from src.types_custom import (
    PredictRequest,
    PredictResponse,
    TicketRequest,
    QRResponse,
    QRValidateRequest,
    QRValidateResponse,
    FraudCheckRequest,
    FraudCheckResponse,
    SearchEventsRequest,
    SearchEventsResponse,
    EventResult,
    DailyReportRequest,
    DailyReportResponse
)
from src.revenue_sharing_service import revenue_sharing_service
from src.revenue_sharing_models import EventRevenueInput, RevenueCalculationResult, RevenueShareConfig
from src.analytics.service import analytics_service
from src.config import get_settings
from typing import List
from src.fraud import check_fraud_rules
from src.mock_events import get_mock_events
from src.search_utils import extract_keywords, filter_events_by_keywords
from src.report_service import generate_daily_report_csv
from datetime import date, datetime
import uuid


app = FastAPI(
    title="Veritix Microservice",
    version="0.1.0",
    description="A microservice backend for the Veritix platform."
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)

# Set up structured logging
LOG_LEVEL = get_settings().LOG_LEVEL
setup_logging(LOG_LEVEL)
logger = logging.getLogger("veritix")

# Global model pipeline; created at startup

model_pipeline: Pipeline | None = None

# Chat endpoints
@app.websocket("/ws/chat/{conversation_id}/{user_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str, user_id: str):
    """WebSocket endpoint for real-time chat."""
    await chat_manager.connect(websocket, conversation_id, user_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                
                # Create chat message
                message = ChatMessage(
                    id=str(uuid.uuid4()),
                    sender_id=user_id,
                    sender_type=message_data.get("sender_type", "user"),
                    content=message_data["content"],
                    timestamp=datetime.utcnow(),
                    conversation_id=conversation_id,
                    metadata=message_data.get("metadata", {})
                )
                
                # Send message to all participants
                await chat_manager.send_message(message)
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from client")
            except KeyError as e:
                logger.warning(f"Missing required field: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id} in conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await chat_manager.disconnect(websocket, conversation_id, user_id)


@app.post("/chat/{conversation_id}/messages")
async def send_message(conversation_id: str, message: dict):
    """Send a message to a conversation (HTTP endpoint)."""
    try:
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            sender_id=message["sender_id"],
            sender_type=message["sender_type"],
            content=message["content"],
            timestamp=datetime.utcnow(),
            conversation_id=conversation_id,
            metadata=message.get("metadata", {})
        )
        
        success = await chat_manager.send_message(chat_message)
        if success:
            return {"status": "success", "message_id": chat_message.id}
        else:
            return {"status": "error", "message": "Failed to send message"}, 500
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"status": "error", "message": str(e)}, 500


@app.get("/chat/{conversation_id}/history")
async def get_message_history(conversation_id: str, limit: int = 50):
    """Get message history for a conversation."""
    try:
        messages = chat_manager.get_message_history(conversation_id, limit)
        return {
            "conversation_id": conversation_id,
            "messages": [msg.dict() for msg in messages],
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Error getting message history: {e}")
        return {"status": "error", "message": str(e)}, 500


@app.post("/chat/{conversation_id}/escalate")
async def escalate_conversation(conversation_id: str, escalation: dict):
    """Escalate a conversation to human support."""
    try:
        reason = escalation.get("reason", "user_request")
        metadata = escalation.get("metadata", {})
        
        escalation_event = await chat_manager.escalate_conversation(
            conversation_id, reason, metadata
        )
        
        return {
            "status": "success",
            "escalation_id": escalation_event.id,
            "reason": escalation_event.reason,
            "timestamp": escalation_event.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error escalating conversation: {e}")
        return {"status": "error", "message": str(e)}, 500


@app.get("/chat/{conversation_id}/escalations")
async def get_escalations(conversation_id: str):
    """Get escalation events for a conversation."""
    try:
        escalations = chat_manager.get_escalations(conversation_id)
        return {
            "conversation_id": conversation_id,
            "escalations": [esc.dict() for esc in escalations],
            "count": len(escalations)
        }
    except Exception as e:
        logger.error(f"Error getting escalations: {e}")
        return {"status": "error", "message": str(e)}, 500


@app.get("/chat/user/{user_id}/conversations")
async def get_user_conversations(user_id: str):
    """Get all conversations for a user."""
    try:
        conversation_ids = chat_manager.get_user_conversations(user_id)
        return {
            "user_id": user_id,
            "conversations": conversation_ids,
            "count": len(conversation_ids)
        }
    except Exception as e:
        logger.error(f"Error getting user conversations: {e}")
        return {"status": "error", "message": str(e)}, 500

mock_user_events: Dict[str, list[str]] = {
    "user1": ["concert_A", "concert_B"],
    "user2": ["concert_B", "concert_C"],
    "user3": ["concert_A", "concert_C", "concert_D"],
    "user4": ["concert_D", "concert_E"],
}

class PredictRequest(BaseModel):
    """Request body for /predict-scalper endpoint.

    Each record represents aggregated event signals for a buyer/session.
    """
    features: List[float] = Field(
        ..., description="Feature vector: e.g., [tickets_per_txn, txns_per_min, avg_price_ratio, account_age_days, zip_mismatch, device_changes]"
    )


class PredictResponse(BaseModel):
    probability: float

class RecommendRequest(BaseModel):  
    user_id: str  


class RecommendResponse(BaseModel):  
    recommendations: List[str]

def generate_synthetic_event_data(num_samples: int = 2000, random_seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic data for scalper detection.

    Features (example semantics):
    0: tickets_per_txn (0-12)
    1: txns_per_min (0-10)
    2: avg_price_ratio (0.5-2.0)
    3: account_age_days (0-3650)
    4: zip_mismatch (0 or 1)
    5: device_changes (0-6)
    """
    rng = np.random.default_rng(random_seed)

    tickets_per_txn = rng.integers(1, 13, size=num_samples)
    txns_per_min = rng.uniform(0, 10, size=num_samples)
    avg_price_ratio = rng.uniform(0.5, 2.0, size=num_samples)
    account_age_days = rng.integers(0, 3651, size=num_samples)
    zip_mismatch = rng.integers(0, 2, size=num_samples)
    device_changes = rng.integers(0, 7, size=num_samples)

    X = np.column_stack([
        tickets_per_txn,
        txns_per_min,
        avg_price_ratio,
        account_age_days,
        zip_mismatch,
        device_changes,
    ])

    # True underlying weights to simulate scalper probability
    weights = np.array([0.35, 0.45, 0.25, -0.002, 0.4, 0.3])
    bias = -2.0
    logits = X @ weights + bias
    probs = 1 / (1 + np.exp(-logits))
    y = rng.binomial(1, probs)
    return X.astype(float), y.astype(int)


def train_logistic_regression_pipeline() -> Pipeline:
    """Train a simple standardize+logistic-regression pipeline on synthetic data."""
    X, y = generate_synthetic_event_data()
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=123)
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, solver="lbfgs")),
        ]
    )
    pipeline.fit(X_train, y_train)
    return pipeline

model_pipeline: Any | None = None
etl_scheduler: "BackgroundScheduler | None" = None

# --- Fraud Detection Endpoint ---
@app.post("/check-fraud", response_model=FraudCheckResponse)
def check_fraud(payload: FraudCheckRequest):
    log_info("Fraud check requested", {"event_count": len(payload.events)})
    triggered = check_fraud_rules(payload.events)
    FRAUD_DETECTIONS_TOTAL.labels(rules_triggered=str(len(triggered))).inc()
    log_info("Fraud check completed", {"triggered_rules": triggered})
    return FraudCheckResponse(triggered_rules=triggered)


# --- Search Events Endpoint ---
@app.post("/search-events", response_model=SearchEventsResponse)
def search_events(payload: SearchEventsRequest):
    """
    Search for events using natural language queries with simple NLP keyword extraction.
    
    Example queries:
    - "music events in Lagos this weekend"
    - "tech conferences in Abuja"
    - "sports events today"
    """
    try:
        # Extract keywords from the query
        keywords = extract_keywords(payload.query)
        
        # Get mock events
        all_events = get_mock_events()
        
        # Filter events based on extracted keywords
        matching_events = filter_events_by_keywords(all_events, keywords)
        
        # Convert to EventResult models
        event_results = [
            EventResult(
                id=event['id'],
                name=event['name'],
                description=event['description'],
                event_type=event['event_type'],
                location=event['location'],
                date=event['date'],
                price=event['price'],
                capacity=event['capacity']
            )
            for event in matching_events
        ]
        
        return SearchEventsResponse(
            query=payload.query,
            results=event_results,
            count=len(event_results),
            keywords_extracted=keywords
        )
    except Exception as exc:
        logger.error("Search events failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Search failed: {exc}"}
        )


@app.get("/stats")
def get_analytics_stats(event_id: str = None):
    """Get analytics statistics for ticket scans, transfers, and invalid attempts per event."""
    log_info("Analytics stats requested", {
        "event_id": event_id
    })
    
    try:
        if event_id:
            # Get stats for specific event
            result = analytics_service.get_stats_for_event(event_id)
            log_info("Analytics stats retrieved for event", {
                "event_id": event_id,
                "scan_count": result.get("scan_count", 0),
                "transfer_count": result.get("transfer_count", 0),
                "invalid_attempt_count": result.get("invalid_attempt_count", 0)
            })
            return result
        else:
            # Get stats for all events
            result = analytics_service.get_stats_for_all_events()
            log_info("Analytics stats retrieved for all events", {
                "event_count": len(result)
            })
            return result
    except Exception as e:
        log_error("Failed to retrieve analytics stats", {
            "event_id": event_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics stats: {str(e)}")


@app.get("/stats/scans")
def get_recent_scans(event_id: str, limit: int = 50):
    """Get recent scan records for an event."""
    log_info("Recent scans requested", {
        "event_id": event_id,
        "limit": limit
    })
    
    try:
        scans = analytics_service.get_recent_scans(event_id, limit)
        log_info("Recent scans retrieved", {
            "event_id": event_id,
            "scan_count": len(scans)
        })
        return {"event_id": event_id, "scans": scans, "count": len(scans)}
    except Exception as e:
        log_error("Failed to retrieve recent scans", {
            "event_id": event_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent scans: {str(e)}")


@app.get("/stats/transfers")
def get_recent_transfers(event_id: str, limit: int = 50):
    """Get recent transfer records for an event."""
    log_info("Recent transfers requested", {
        "event_id": event_id,
        "limit": limit
    })
    
    try:
        transfers = analytics_service.get_recent_transfers(event_id, limit)
        log_info("Recent transfers retrieved", {
            "event_id": event_id,
            "transfer_count": len(transfers)
        })
        return {"event_id": event_id, "transfers": transfers, "count": len(transfers)}
    except Exception as e:
        log_error("Failed to retrieve recent transfers", {
            "event_id": event_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent transfers: {str(e)}")


@app.get("/stats/invalid-attempts")
def get_invalid_attempts(event_id: str, limit: int = 50):
    """Get recent invalid attempt records for an event."""
    log_info("Invalid attempts requested", {
        "event_id": event_id,
        "limit": limit
    })
    
    try:
        attempts = analytics_service.get_invalid_attempts(event_id, limit)
        log_info("Invalid attempts retrieved", {
            "event_id": event_id,
            "attempt_count": len(attempts)
        })
        return {"event_id": event_id, "attempts": attempts, "count": len(attempts)}
    except Exception as e:
        log_error("Failed to retrieve invalid attempts", {
            "event_id": event_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to retrieve invalid attempts: {str(e)}")


@app.on_event("startup")
def on_startup() -> None:
    global model_pipeline
    settings = get_settings()
    # Allow test environments to skip expensive model training / ML imports
    skip_training = settings.SKIP_MODEL_TRAINING
    if not skip_training:
        model_pipeline = train_logistic_regression_pipeline()
    # Optionally start ETL scheduler
    enable_sched = settings.ENABLE_ETL_SCHEDULER
    if enable_sched and BackgroundScheduler:
        global etl_scheduler
        etl_scheduler = BackgroundScheduler(timezone="UTC")
        cron = settings.ETL_CRON
        if cron and CronTrigger:
            trigger = CronTrigger.from_crontab(cron)
        else:
            minutes = settings.ETL_INTERVAL_MINUTES
            trigger = IntervalTrigger(minutes=minutes)
        etl_scheduler.add_job(run_etl_once, trigger=trigger, id="etl_job", replace_existing=True)
        etl_scheduler.start()

@app.get("/")
def read_root():
    return {"message": "Veritix Service is running. Check /health for status."}

@app.get("/health", status_code=200)
def health_check():
    log_info("Health check requested")
    return JSONResponse(content={
        "status": "OK",
        "service": "Veritix Backend",
        "api_version": app.version
    })


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    log_info("Metrics endpoint requested")
    return PlainTextResponse(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


@app.post("/predict-scalper", response_model=PredictResponse)
def predict_scalper(payload: PredictRequest):
    log_info("Scalper prediction requested", {"feature_count": len(payload.features)})
    if model_pipeline is None:
        log_error("Model not ready for prediction")
        return JSONResponse(status_code=503, content={"detail": "Model not ready"})
    features = np.array(payload.features, dtype=float).reshape(1, -1)
    proba = float(model_pipeline.predict_proba(features)[0, 1])
    log_info("Scalper prediction completed", {"probability": proba})
    return PredictResponse(probability=proba)

# If you run this file directly (e.g., in a local development environment outside Docker):
# if __name__ == "__main__":
#     import uvicorn
#     # Note: host="0.0.0.0" is crucial for Docker development
#     uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/recommend-events", response_model=RecommendResponse)  
def recommend_events(payload: RecommendRequest):  
    user_id = payload.user_id  
    if user_id not in mock_user_events:  
        raise HTTPException(  
            status_code=404,  
            detail={"message": "User not found"}  
        )  
    user_events = set(mock_user_events[user_id])  
    scores = {}  
    for other_user, events in mock_user_events.items():  
        if other_user == user_id:  
            continue  
        overlap = len(user_events.intersection(events))  
        for e in events:  
            if e not in user_events:  
                scores[e] = scores.get(e, 0) + overlap  

    recommended = sorted(scores, key=scores.get, reverse=True)[:3]  
    return RecommendResponse(recommendations=recommended)  

    global model_pipeline
    try:
        if model_pipeline is None:
            # Lazy-initialize the model to ensure availability in test environments
            model_pipeline = train_logistic_regression_pipeline()
        # import numpy locally to avoid importing it at module import time
        import numpy as np
        features = np.array(payload.features, dtype=float).reshape(1, -1)
        proba = float(model_pipeline.predict_proba(features)[0, 1])
        return PredictResponse(probability=proba)
    except Exception as exc:
        # Return 500 on errors (e.g., invalid feature length) to align with tests
        return JSONResponse(status_code=500, content={"detail": f"Prediction failed: {exc}"})


@app.post("/generate-qr", response_model=QRResponse)
def generate_qr(payload: TicketRequest):
    log_info("QR code generation requested", {
        "ticket_id": payload.ticket_id,
        "event": payload.event,
        "user": payload.user
    })
    # Encode ticket metadata as compact JSON
    unsigned = {
        "ticket_id": payload.ticket_id,
        "event": payload.event,
        "user": payload.user,
    }
    sig = compute_signature(unsigned)
    data = {**unsigned, "sig": sig}
    # Lazy import to avoid requiring pillow/qrcode for all test runs
    try:
        import qrcode as _qrcode
        from PIL import Image  # noqa: F401 - pillow is used by qrcode
    except Exception as exc:
        # If qrcode isn't installed, return a helpful error (tests expecting QR generation
        # should install the dependency). The endpoint returns 500 to align with other errors.
        log_warning("QR generation skipped - missing dependency", {"error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "QR generation dependency missing"})

    qr = _qrcode.QRCode(error_correction=_qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(json.dumps(data, separators=(",", ":")))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    QR_GENERATIONS_TOTAL.inc()
    log_info("QR code generated successfully")
    return QRResponse(qr_base64=encoded)


@app.post("/validate-qr", response_model=QRValidateResponse)
def validate_qr(payload: QRValidateRequest):
    log_info("QR validation requested")
    try:
        data = json.loads(payload.qr_text)
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
            return QRValidateResponse(isValid=True, metadata=unsigned)
        log_warning("Invalid QR signature", {"metadata": unsigned})
        QR_VALIDATIONS_TOTAL.labels(result="invalid").inc()
        return QRValidateResponse(isValid=False)
    except Exception as exc:
        log_warning("Invalid QR validation attempt", {"error": str(exc)})
        QR_VALIDATIONS_TOTAL.labels(result="error").inc()
        return QRValidateResponse(isValid=False)


@app.post("/generate-daily-report", response_model=DailyReportResponse)
def generate_daily_report(payload: DailyReportRequest):
    try:
        # Parse target_date
        target_date = None
        if payload.target_date:
            try:
                target_date = date.fromisoformat(payload.target_date)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid date format. Use YYYY-MM-DD."}
                )
        else:
            target_date = date.today()
        
        # Validate output format
        if payload.output_format not in ["csv", "json"]:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid output_format. Use 'csv' or 'json'."}
            )
        
        # Generate report
        report_path = generate_daily_report_csv(
            target_date=target_date,
            output_format=payload.output_format
        )
        
        # Query summary stats for response
        from src.report_service import _query_daily_sales, _query_transfer_stats, _query_invalid_scans
        sales_data = _query_daily_sales(target_date)
        transfer_stats = _query_transfer_stats(target_date)
        invalid_scan_stats = _query_invalid_scans(target_date)
        
        total_sales = sum(row["tickets_sold"] for row in sales_data)
        total_revenue = sum(row["revenue"] for row in sales_data)
        
        return DailyReportResponse(
            success=True,
            report_path=report_path,
            report_date=str(target_date),
            summary={
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "total_transfers": transfer_stats.get("total_transfers", 0),
                "invalid_scans": invalid_scan_stats.get("invalid_scans", 0)
            },
            message=f"Report generated successfully at {report_path}"
        )
    
    except Exception as exc:
        log_error("Daily report generation failed", {"error": str(exc)})
        return JSONResponse(
            status_code=500,
            content={"detail": f"Report generation failed: {exc}"}
        )


@app.post("/calculate-revenue-share", response_model=RevenueCalculationResult)
def calculate_revenue_share(input_data: EventRevenueInput):
    """Calculate revenue shares for stakeholders based on event sales and smart contract rules."""
    log_info("Revenue share calculation requested", {
        "event_id": input_data.event_id,
        "total_sales": input_data.total_sales,
        "ticket_count": input_data.ticket_count
    })
    
    # Validate input
    is_valid, errors = revenue_sharing_service.validate_input(input_data)
    if not is_valid:
        log_error("Revenue share calculation validation failed", {"errors": errors})
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    try:
        result = revenue_sharing_service.calculate_revenue_shares(input_data)
        log_info("Revenue share calculation successful", {
            "event_id": input_data.event_id,
            "total_paid_out": result.total_paid_out,
            "stakeholder_count": len(result.distributions)
        })
        return result
    except Exception as e:
        log_error("Revenue share calculation failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Revenue calculation failed: {str(e)}")


@app.post("/calculate-revenue-share/batch", response_model=List[RevenueCalculationResult])
def calculate_revenue_share_batch(inputs: List[EventRevenueInput]):
    """Calculate revenue shares for multiple events."""
    log_info("Batch revenue share calculation requested", {
        "event_count": len(inputs)
    })
    
    results = []
    for input_data in inputs:
        try:
            is_valid, errors = revenue_sharing_service.validate_input(input_data)
            if not is_valid:
                log_error("Batch revenue calculation validation failed", {
                    "event_id": input_data.event_id,
                    "errors": errors
                })
                continue
            
            result = revenue_sharing_service.calculate_revenue_shares(input_data)
            results.append(result)
        except Exception as e:
            log_error("Batch revenue calculation failed", {
                "event_id": input_data.event_id,
                "error": str(e)
            })
            continue
    
    log_info("Batch revenue share calculation completed", {
        "processed_count": len(results),
        "requested_count": len(inputs)
    })
    
    return results


@app.get("/revenue-share/config", response_model=RevenueShareConfig)
def get_revenue_share_config():
    """Get the current revenue sharing configuration."""
    log_info("Revenue share configuration requested")
    return revenue_sharing_service.config


@app.get("/revenue-share/example", response_model=EventRevenueInput)
def get_example_revenue_input():
    """Get an example revenue calculation input."""
    log_info("Revenue share example input requested")
    return EventRevenueInput(
        event_id="event_123",
        total_sales=10000.0,
        ticket_count=100,
        currency="USD",
        additional_fees={"service_fee": 50.0}
    )


@app.on_event("shutdown")
def on_shutdown() -> None:
    global etl_scheduler
    if etl_scheduler:
        try:
            etl_scheduler.shutdown(wait=False)
        except Exception:
            pass
