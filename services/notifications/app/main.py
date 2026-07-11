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
from shiftmaster_common.middleware.setup import CorrelationIdMiddleware, app_exception_handler, validation_exception_handler, unhandled_exception_handler
from fastapi.exceptions import RequestValidationError
from shiftmaster_common.middleware.exceptions import AppException

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
    title="ShiftMaster-py Notification API",
    version="1.0.0",
    description="""
    Microservice handling audit logs and asynchronous notifications.
    """,
    lifespan=lifespan,
    docs_url="/api/v1/notifications/docs",
    openapi_url="/api/v1/notifications/openapi.json",
    openapi_tags=[
        {"name": "Audit Logs", "description": "Read-only access to system audit logs"},
        {"name": "Notifications", "description": "Manage user notifications"},
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


from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/swagger-login",
                    "scopes": {}
                }
            }
        }
    }
    for path in openapi_schema.get("paths", {}):
        for method in openapi_schema["paths"][path]:
            if "health" not in path and "swagger-login" not in path and "login" not in path:
                openapi_schema["paths"][path][method]["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
