from fastapi import APIRouter, Depends, Request

from src.auth.dependencies import require_service_key
from src.core.ratelimit import limiter

router = APIRouter(prefix="/qr", tags=["QR"])


@router.post("/verify")
@limiter.limit("30/minute")
async def verify_qr(request: Request) -> dict[str, object]:
    """Public endpoint for scanning/verifying a QR ticket."""
    return {"success": True, "msg": "QR verified successfully"}


@router.post("/generate", dependencies=[Depends(require_service_key)])
@limiter.limit("60/minute")
async def generate_qr(request: Request) -> dict[str, object]:
    """Protected endpoint for generating a new QR ticket."""
    return {"success": True, "msg": "QR generated successfully"}