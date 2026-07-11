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
from app.api.routers import auth, employees, departments

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("auth_service.starting")
    await create_pool()
    await init_redis(url=settings.redis.url)
    await init_rabbitmq(url=settings.rabbitmq.url)
    
    logger.info("auth_service.ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("auth_service.stopping")
    await close_rabbitmq()
    await close_pool()
    await close_redis()
    logger.info("auth_service.stopped")

app = FastAPI(
    title="ShiftMaster Auth Service API",
    version="1.0.0",
    description="""
    Microservice handling user authentication, authorization, and employee management.
    """,
    lifespan=lifespan,
    docs_url="/api/v1/auth/docs",
    openapi_url="/api/v1/auth/openapi.json",
    openapi_tags=[
        {"name": "Authentication", "description": "Login and session management"},
        {"name": "Employees", "description": "Manage employee records and roles"},
        {"name": "Departments", "description": "Manage organizational departments"},
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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(employees.router, prefix="/api/v1/employees", tags=["Employees"])
app.include_router(departments.router, prefix="/api/v1/departments", tags=["Departments"])

@app.get("/api/v1/auth/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "auth"}


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
