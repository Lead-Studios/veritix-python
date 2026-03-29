"""Router for POST /check-fraud/batch — process multiple fraud-check requests in one call."""
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.fraud import check_fraud_rules, determine_severity

router = APIRouter(tags=["Fraud"])


class BatchFraudItem(BaseModel):
    """A single set of events to evaluate for fraud."""

    request_id: str = Field(..., description="Caller-supplied identifier for this item.")
    events: List[Dict[str, Any]] = Field(..., description="List of ticket events to evaluate.")


class BatchFraudResult(BaseModel):
    """Fraud-check result for one item in the batch."""

    request_id: str
    triggered_rules: List[str]
    severity: str


class BatchFraudRequest(BaseModel):
    items: List[BatchFraudItem] = Field(..., description="Batch of fraud-check requests.")


class BatchFraudResponse(BaseModel):
    results: List[BatchFraudResult]


@router.post("/check-fraud/batch", response_model=BatchFraudResponse)
def check_fraud_batch(payload: BatchFraudRequest) -> BatchFraudResponse:
    """Evaluate multiple sets of ticket events for fraud in a single request."""
    results = []
    for item in payload.items:
        triggered = check_fraud_rules(item.events)
        severity = determine_severity(triggered)
        results.append(
            BatchFraudResult(
                request_id=item.request_id,
                triggered_rules=triggered,
                severity=severity,
            )
        )
    return BatchFraudResponse(results=results)
