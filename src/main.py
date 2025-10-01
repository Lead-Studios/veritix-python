from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from typing import Dict, List

app = FastAPI(
    title="Veritix Microservice",
    version="0.1.0",
    description="A microservice backend for the Veritix platform."
)

# Global model pipeline; created at startup
model_pipeline: Pipeline | None = None

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