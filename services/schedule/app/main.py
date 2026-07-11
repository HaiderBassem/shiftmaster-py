from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware

from shiftmaster_common.middleware.setup import unhandled_exception_handler
from shiftmaster_common.logging.structured import get_logger
from shiftmaster_common.messaging.rabbitmq import init_rabbitmq, close_rabbitmq
from shiftmaster_common.cache.redis_client import init_redis, close_redis
from app.core.config import settings
from app.db.pool import create_pool, close_pool
from app.api.routers import schedules, shifts, handovers
from app.events.consumers import start_consumers
from shiftmaster_common.middleware.openapi import setup_custom_openapi
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("schedule_service.starting")
    await create_pool()
    await init_redis(url=settings.redis.url)
    await init_rabbitmq(url=settings.rabbitmq.url)
    await start_consumers()
    
    logger.info("schedule_service.ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("schedule_service.stopping")
    await close_rabbitmq()
    await close_pool()
    await close_redis()
    logger.info("schedule_service.stopped")

app = FastAPI(
    title="ShiftMaster-py Schedule API",
    description="""
    Microservice handling scheduling, shifts, and handovers.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/schedule/docs",
    openapi_url="/api/v1/schedule/openapi.json",
    openapi_tags=[
        {"name": "Schedules", "description": "Manage work schedules"},
        {"name": "Shifts", "description": "Manage individual shifts"},
        {"name": "Handovers", "description": "Shift handovers between employees"},
    ]
)

# Exception handler
app.add_exception_handler(Exception, unhandled_exception_handler)

# Middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Correlation-ID"],
    expose_headers=["X-Correlation-ID"],
)

# API Routers
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["Schedules"])
app.include_router(shifts.router, prefix="/api/v1/shifts", tags=["Shifts"])
app.include_router(handovers.router, prefix="/api/v1/handovers", tags=["Handovers"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "schedule"}


setup_custom_openapi(app)
