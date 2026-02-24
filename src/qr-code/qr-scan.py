import os
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import FastAPI


def _debug_enabled() -> bool:
    return os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}


def _http_error_message(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        for key in ("message", "detail", "error"):
            value = detail.get(key)
            if isinstance(value, str) and value:
                return value
    return "HTTP error"


async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": _http_error_message(exc.detail),
            "status_code": exc.status_code,
        },
    )


async def handle_validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field = ".".join(str(item) for item in loc if item != "body")
        field_errors.append(
            {
                "field": field or "body",
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "validation_error"),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "status_code": 422,
            "detail": field_errors,
        },
    )


async def handle_unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    detail = str(exc) if _debug_enabled() else None
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": detail,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(Exception, handle_unhandled_exception)
