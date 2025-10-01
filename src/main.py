from fastapi import FastAPI
from fastapi.responses import JSONResponse
import base64
import io
import json
import qrcode
import hmac
import logging
import numpy as np
from sklearn.pipeline import Pipeline

from src.utils import compute_signature, train_logistic_regression_pipeline
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
model_pipeline: Pipeline | None = None

# --- Fraud Detection Endpoint ---
@app.post("/check-fraud", response_model=FraudCheckResponse)
def check_fraud(payload: FraudCheckRequest):
    triggered = check_fraud_rules(payload.events)
    return FraudCheckResponse(triggered_rules=triggered)




@app.on_event("startup")
def on_startup() -> None:
    global model_pipeline
    model_pipeline = train_logistic_regression_pipeline()

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
    if model_pipeline is None:
        return JSONResponse(status_code=503, content={"detail": "Model not ready"})
    features = np.array(payload.features, dtype=float).reshape(1, -1)
    proba = float(model_pipeline.predict_proba(features)[0, 1])
    return PredictResponse(probability=proba)


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
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
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
