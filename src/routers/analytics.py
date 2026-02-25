from datetime import datetime, timezone
from typing import Optional

from cachetools import TTLCache  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.dependencies import require_admin_key

# ---------------------------------------------------------------------------
# NOTE: get_db / get_current_user / ORM models are mocked here because the
# analytics router is a thin layer over the actual analytics service in
# src/analytics/service.py.  Replace these stubs with real imports when wiring
# up the router to the application database session.
# ---------------------------------------------------------------------------

def get_db() -> None:  # type: ignore[return]
    """Stub – replace with real SQLAlchemy session dependency."""
    pass


def get_current_user() -> dict[str, object]:  # type: ignore[return]
    """Stub – replace with real authentication dependency."""
    pass


class _EventSalesSummaryStub:
    id: None = None
    total_tickets_sold: None = None
    revenue_xlm: None = None
    revenue_usd: None = None


class _EtlRunLogStub:
    created_at: None = None


router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Cache: at most 1 result, TTL = 60 seconds
summary_cache: TTLCache[str, "AnalyticsSummaryResponse"] = TTLCache(maxsize=1, ttl=60)


class AnalyticsSummaryResponse(BaseModel):
    total_events: int
    total_tickets_sold: int
    total_revenue_xlm: str
    total_revenue_usd: str
    last_etl_at: Optional[datetime]
    generated_at: datetime


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: dict[str, object] = Depends(get_current_user),
) -> AnalyticsSummaryResponse:
    """Return a platform-wide aggregated analytics summary (cached 60 s)."""
    from sqlalchemy import func  # noqa: PLC0415

    cached = summary_cache.get("summary_data")
    if cached:
        return cached

    EventSalesSummary = _EventSalesSummaryStub  # noqa: N806 – matches ORM model naming
    EtlRunLog = _EtlRunLogStub  # noqa: N806

    sales_agg = db.query(  # type: ignore[union-attr]
        func.count(EventSalesSummary.id).label("total_events"),
        func.sum(EventSalesSummary.total_tickets_sold).label("total_tickets"),
        func.sum(EventSalesSummary.revenue_xlm).label("total_xlm"),
        func.sum(EventSalesSummary.revenue_usd).label("total_usd"),
    ).first()

    last_etl = db.query(func.max(EtlRunLog.created_at)).scalar()  # type: ignore[union-attr]

    total_events: int = sales_agg.total_events or 0 if sales_agg else 0
    total_tickets_sold: int = sales_agg.total_tickets or 0 if sales_agg else 0
    total_revenue_xlm: str = str(sales_agg.total_xlm or "0.00") if sales_agg else "0.00"
    total_revenue_usd: str = str(sales_agg.total_usd or "0.00") if sales_agg else "0.00"

    response = AnalyticsSummaryResponse(
        total_events=total_events,
        total_tickets_sold=total_tickets_sold,
        total_revenue_xlm=total_revenue_xlm,
        total_revenue_usd=total_revenue_usd,
        last_etl_at=last_etl,
        generated_at=datetime.now(timezone.utc),
    )

    summary_cache["summary_data"] = response
    return response