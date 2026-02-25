"""Health and readiness endpoints.

GET /health  — liveness probe; always 200.
GET /ready   — readiness probe; 200 when all deps are reachable, 503 otherwise.
Both endpoints are intentionally free of auth and rate-limiting.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.analytics.models import get_engine
from src.config import get_settings

logger = logging.getLogger("veritix.health")

router = APIRouter(tags=["Health"])

_SERVICE_NAME = "veritix-python"
_NEST_TIMEOUT = 5.0  # seconds


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# /health — liveness probe
# ---------------------------------------------------------------------------


@router.get("/health", status_code=200)
def health() -> JSONResponse:
    """Always returns 200 so orchestrators know the process is alive."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": _SERVICE_NAME,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# /ready — readiness probe
# ---------------------------------------------------------------------------


def _check_database() -> str:
    """Return 'ok' if a SELECT 1 succeeds, otherwise 'error'."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness database check failed: %s", exc)
        return "error"


def _check_nest_api() -> str:
    """Return 'ok' if the NestJS /health endpoint responds within timeout."""
    try:
        base_url = get_settings().NEST_API_BASE_URL.rstrip("/")
        response = httpx.get(f"{base_url}/health", timeout=_NEST_TIMEOUT)
        # Any HTTP response (even non-2xx) means the service is reachable.
        return "ok"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness NestJS API check failed: %s", exc)
        return "error"


@router.get("/ready")
def ready() -> JSONResponse:
    """Readiness probe — checks database and NestJS API connectivity."""
    checks: Dict[str, str] = {
        "database": _check_database(),
        "nest_api": _check_nest_api(),
    }

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ok else "not_ready",
            "checks": checks,
            "timestamp": _now_iso(),
        },
    )