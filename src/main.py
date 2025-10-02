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

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
except Exception:
    BackgroundScheduler = None
    CronTrigger = None
    IntervalTrigger = None
from src.types import (
    PredictRequest,
    PredictResponse,
    TicketRequest,
    QRResponse,
    QRValidateRequest,
    QRValidateResponse,
    FraudCheckRequest,
    FraudCheckResponse
)
from src.fraud import check_fraud_rules

app = FastAPI(
    title="Veritix Microservice",
    version="0.1.0",
    description="A microservice backend for the Veritix platform."
)

logger = logging.getLogger("veritix")

# Global model pipeline; created at startup
model_pipeline: Any | None = None
etl_scheduler: "BackgroundScheduler | None" = None

# --- Fraud Detection Endpoint ---
@app.post("/check-fraud", response_model=FraudCheckResponse)
def check_fraud(payload: FraudCheckRequest):
    triggered = check_fraud_rules(payload.events)
    return FraudCheckResponse(triggered_rules=triggered)




@app.on_event("startup")
def on_startup() -> None:
    global model_pipeline
    # Allow test environments to skip expensive model training / ML imports
    skip_training = os.getenv("SKIP_MODEL_TRAINING", "false").lower() in ("1", "true", "yes")
    if not skip_training:
        model_pipeline = train_logistic_regression_pipeline()
    # Optionally start ETL scheduler
    enable_sched = os.getenv("ENABLE_ETL_SCHEDULER", "false").lower() in ("true", "1", "yes")
    if enable_sched and BackgroundScheduler:
        global etl_scheduler
        etl_scheduler = BackgroundScheduler(timezone="UTC")
        cron = os.getenv("ETL_CRON")
        if cron and CronTrigger:
            trigger = CronTrigger.from_crontab(cron)
        else:
            minutes = int(os.getenv("ETL_INTERVAL_MINUTES", "15"))
            trigger = IntervalTrigger(minutes=minutes)
        etl_scheduler.add_job(run_etl_once, trigger=trigger, id="etl_job", replace_existing=True)
        etl_scheduler.start()

@app.get("/")
def read_root():
    return {"message": "Veritix Service is running. Check /health for status."}

@app.get("/health", status_code=200)
def health_check():
    return JSONResponse(content={
        "status": "OK",
        "service": "Veritix Backend",
        "api_version": app.version
    })


@app.post("/predict-scalper", response_model=PredictResponse)
def predict_scalper(payload: PredictRequest):
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
        logger.warning("QR generation skipped - missing dependency: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "QR generation dependency missing"})

    qr = _qrcode.QRCode(error_correction=_qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(json.dumps(data, separators=(",", ":")))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return QRResponse(qr_base64=encoded)


@app.post("/validate-qr", response_model=QRValidateResponse)
def validate_qr(payload: QRValidateRequest):
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
            return QRValidateResponse(isValid=True, metadata=unsigned)
        logger.warning("Invalid QR signature", extra={"metadata": unsigned})
        return QRValidateResponse(isValid=False)
    except Exception as exc:
        logger.warning("Invalid QR validation attempt: %s", str(exc))
        return QRValidateResponse(isValid=False)


@app.on_event("shutdown")
def on_shutdown() -> None:
    global etl_scheduler
    if etl_scheduler:
        try:
            etl_scheduler.shutdown(wait=False)
        except Exception:
            pass
