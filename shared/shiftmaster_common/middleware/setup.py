"""
Application middleware stack.

Registered in app/main.py via `app.add_middleware(...)` or
`app.middleware("http")(fn)` in the order they are called here.

Middleware (executed outer → inner on request, inner → outer on response):

  1. CorrelationIdMiddleware  — attaches / generates X-Correlation-ID header
  2. RequestLoggingMiddleware — logs method, path, status, latency in structured JSON
  3. ExceptionHandlerMiddleware — converts AppException subclasses → JSON error body

Global exception handlers (registered with `app.add_exception_handler`):

  * AppException → 4xx JSON
  * RequestValidationError → 422 JSON (Pydantic)
  * Unhandled Exception → 500 JSON (never leaks stack traces)
"""

from __future__ import annotations

import time
import uuid
import logging
from collections.abc import Callable

from asgi_correlation_id import CorrelationIdMiddleware  # re-exported for convenience
from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class AppException(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code

from shiftmaster_common.logging.structured import get_logger
logger = get_logger(__name__)

# ── Re-export so main.py only imports from here ──────────────────────────────
__all__ = [
    "CorrelationIdMiddleware",
    "RequestLoggingMiddleware",
    "app_exception_handler",
    "validation_exception_handler",
    "unhandled_exception_handler",
]


# ── Request logging ───────────────────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request/response with:
      - method, path, query string
      - status code
      - duration in milliseconds
      - correlation_id (automatically included via structlog contextvars)

    Skips the /health endpoint to avoid log noise.
    """

    _SKIP_PATHS = {"/health", "/metrics"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self._SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            query=str(request.url.query) or None,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else None,
        )
        return response


# ── Exception handlers ────────────────────────────────────────────────────────

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Converts any AppException (NotFoundError, ForbiddenError, etc.)
    into a consistent JSON error envelope.
    """
    logger.warning(
        "app.exception",
        status_code=exc.status_code,
        message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error": type(exc).__name__},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Formats Pydantic validation errors in a flat, readable structure."""
    errors = [
        {
            "field": ".".join(str(loc) for loc in e["loc"]),
            "message": e["msg"],
            "type": e["type"],
        }
        for e in exc.errors()
    ]
    logger.warning(
        "request.validation_error",
        path=request.url.path,
        error_count=len(errors),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last-resort handler for any exception that wasn't caught upstream.
    Logs the full traceback but returns a safe, opaque 500 to the client.
    """
    logger.exception(
        "unhandled.exception",
        path=request.url.path,
        method=request.method,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error": "InternalServerError",
        },
    )
