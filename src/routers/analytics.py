from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from cachetools import TTLCache
from typing import Optional
from pydantic import BaseModel

# --- IMPORTANT: Adjust these imports to match your actual project structure ---
# from src.database import get_db
# from src.auth import get_current_user
# from src.models import EventSalesSummary, EtlRunLog
# ------------------------------------------------------------------------------

# Mocked dependencies for illustration - replace with your actual imports
def get_db(): pass
def get_current_user(): pass
class EventSalesSummary:
    id = None
    total_tickets_sold = None
    revenue_xlm = None
    revenue_usd = None
class EtlRunLog:
    created_at = None

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# In-memory cache: stores up to 1 result with a Time-To-Live (TTL) of 60 seconds
summary_cache = TTLCache(maxsize=1, ttl=60)

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
    current_user: dict = Depends(get_current_user)  # Protects with Bearer Auth
):
    # 1. Check Cache first to avoid heavy aggregation
    cached_data = summary_cache.get("summary_data")
    if cached_data:
        return cached_data

    # 2. Database Queries (Single SQL Aggregation)
    sales_agg = db.query(
        func.count(EventSalesSummary.id).label("total_events"),
        func.sum(EventSalesSummary.total_tickets_sold).label("total_tickets"),
        func.sum(EventSalesSummary.revenue_xlm).label("total_xlm"),
        func.sum(EventSalesSummary.revenue_usd).label("total_usd")
    ).first()

    # Get the latest ETL run timestamp
    last_etl = db.query(func.max(EtlRunLog.created_at)).scalar()

    # 3. Handle potential None values (if tables are empty)
    total_events = sales_agg.total_events or 0
    total_tickets_sold = sales_agg.total_tickets or 0
    
    # 4. Format revenues strictly as strings to prevent floating-point precision issues
    # Ensure they maintain standard decimal formatting
    total_revenue_xlm = str(sales_agg.total_xlm or "0.00")
    total_revenue_usd = str(sales_agg.total_usd or "0.00")

    # 5. Construct Response
    response = AnalyticsSummaryResponse(
        total_events=total_events,
        total_tickets_sold=total_tickets_sold,
        total_revenue_xlm=total_revenue_xlm,
        total_revenue_usd=total_revenue_usd,
        last_etl_at=last_etl,
        generated_at=datetime.now(timezone.utc)
    )

    # 6. Store in Cache
    summary_cache["summary_data"] = response

    return response