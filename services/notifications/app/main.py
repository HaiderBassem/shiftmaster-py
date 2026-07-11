import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import settings
from app.db.pool import create_pool, close_pool

from shiftmaster_common.logging.structured import configure_logging, get_logger
from shiftmaster_common.middleware.correlation_id import CorrelationIdMiddleware
from shiftmaster_common.middleware.error_handler import app_exception_handler, validation_exception_handler, unhandled_exception_handler
from fastapi.exceptions import RequestValidationError
from shiftmaster_common.exceptions.app_exceptions import AppException

from app.events.consumer import start_consumers
from shiftmaster_common.messaging.rabbitmq import init_rabbitmq, close_rabbitmq
from shiftmaster_common.cache.redis_client import init_redis, close_redis
from app.api.routers import audit, notifications

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    configure_logging(dev_mode=settings.server.is_development)
    logger.info("app.starting", project=settings.project_name, env=settings.server.env)

    await create_pool()
    await init_redis(settings.redis.url)
    await init_rabbitmq(settings.rabbitmq.url)
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
    title=settings.project_name,
    version="0.1.0",
    description="Shiftmaster-py — Notification Service",
    lifespan=lifespan,
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

app.add_middleware(CorrelationIdMiddleware)

# ── Global exception handlers ─────────────────────────────────────────────────

app.add_exception_handler(AppException, app_exception_handler)                  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(audit.router, prefix=f"{settings.api_v1_str}/audit", tags=["Audit Logs"])
app.include_router(notifications.router, prefix=f"{settings.api_v1_str}/notifications", tags=["Notifications"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "project": settings.project_name,
        "env": settings.server.env,
    }
