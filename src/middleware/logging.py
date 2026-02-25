import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api.request_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Exclude GET /health to avoid log spam
        if request.method == "GET" and request.url.path == "/health":
            return await call_next(request)

        start_time = time.time()
        response: Response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        log_data: dict[str, object] = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        is_debug = os.getenv("DEBUG", "False").lower() == "true"
        if is_debug:
            safe_headers = {
                k: v
                for k, v in request.headers.items()
                if k.lower() != "authorization"
            }
            log_data["headers"] = safe_headers  # type: ignore[assignment]

        logger.info(json.dumps(log_data))
        return response