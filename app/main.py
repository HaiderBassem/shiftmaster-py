import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.db.pool import create_pool, close_pool
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up database pool...")
    await create_pool()
    yield
    # Shutdown
    print("Shutting down database pool...")
    await close_pool()

app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="Shiftmaster-py",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
app.include_router(api_router, prefix=settings.api_v1_str)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "project": settings.project_name}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="localhost", port=5353, reload=True)
