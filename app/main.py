"""
Application entrypoint.

Lifespan order (startup):
  1. configure_logging   — structlog JSON / console renderer
  2. create_pool         — Postgres async pool (with tenacity retries)
  3. init_redis          — Redis connection pool

Middleware stack (outer → inner):
  1. CORSMiddleware
  2. CorrelationIdMiddleware  — injects / reads X-Correlation-ID header
  3. RequestLoggingMiddleware — structured JSON request/response log

Exception handlers (registered globally, eliminating per-router boilerplate):
  * AppException         → 4xx JSON
  * RequestValidationError → 422 JSON
  * Exception            → 500 JSON (no stack trace leakage)
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.exceptions import AppException
from app.core.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    app_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.db.pool import create_pool, close_pool
from app.core.redis import init_redis, close_redis
from app.events.broker import init_rabbitmq, close_rabbitmq
from app.events.consumers import start_consumers
from app.api.routers import tasks, audit

from shiftmaster_common.middleware.openapi import setup_custom_openapi
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    configure_logging(dev_mode=settings.server.is_development)
    logger.info("app.starting", project=settings.project_name, env=settings.server.env)

    await create_pool()
    await init_redis()
    await init_rabbitmq()
    await start_consumers()

    logger.info("app.ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("app.stopping")
    await close_rabbitmq()
    await close_pool()
    await close_redis()
    logger.info("app.stopped")


app = FastAPI(
    title="ShiftMaster-py Core API",
    version="1.0.0",
    description="""
    Core monolith service handling legacy operations before microservice extraction.
    Currently manages Tasks.
    """,
    lifespan=lifespan,
    docs_url="/api/v1/monolith/docs",
    openapi_url="/api/v1/monolith/openapi.json",
    openapi_tags=[
        {"name": "Tasks", "description": "Manage user tasks and boards"},
    ]
)

# ── Middleware (order matters: first registered = outermost) ──────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Correlation-ID"],
    expose_headers=["X-Correlation-ID"],
)

# Correlation ID — must be inside CORS so the header is available to all
app.add_middleware(CorrelationIdMiddleware)

# Request/response structured logging
app.add_middleware(RequestLoggingMiddleware)

# ── Global exception handlers ─────────────────────────────────────────────────

app.add_exception_handler(AppException, app_exception_handler)                  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
# API Routers
app.include_router(tasks.router, prefix=f"{settings.api_v1_str}/tasks", tags=["Tasks"])
app.include_router(audit.router, prefix=f"{settings.api_v1_str}/audit", tags=["Audit"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "project": settings.project_name,
        "env": settings.server.env,
    }


setup_custom_openapi(app)
