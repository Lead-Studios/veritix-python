import time
import json
import logging
import os
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Initialize standard Python logger
logger = logging.getLogger("api.request_logger")
logger.setLevel(logging.INFO)

# Ensure it has a handler if not already configured elsewhere
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Exclude GET /health to avoid log spam
        if request.method == "GET" and request.url.path == "/health":
            return await call_next(request)

        # 2. Record start time
        start_time = time.time()

        # 3. Process the request
        # Note: We NEVER read await request.body() here to strictly avoid logging PII
        response = await call_next(request)

        # 4. Record end time and calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # 5. Build the structured JSON log
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 6. Add headers if in DEBUG mode (excluding Authorization)
        is_debug = os.getenv("DEBUG", "False").lower() == "true"
        if is_debug:
            safe_headers = {
                k: v for k, v in request.headers.items() 
                if k.lower() != "authorization"
            }
            log_data["headers"] = safe_headers

        # 7. Log the structured data
        logger.info(json.dumps(log_data))

        return response