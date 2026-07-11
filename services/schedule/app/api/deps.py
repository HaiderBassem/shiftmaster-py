from fastapi import Depends, HTTPException, status, Header
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from redis.asyncio import Redis

import app.db.pool as db_module
from shiftmaster_common.cache.redis_client import get_redis as _get_redis

from app.repositories.schedule_repo import ScheduleRepository
from app.services.schedule_service import ScheduleService
from app.repositories.shift_repo import ShiftRepository
from app.services.shift_service import ShiftService
from app.repositories.handover_repo import HandoverRepository
from app.services.handover_service import HandoverService



def get_db_pool() -> AsyncConnectionPool:
    if db_module.pool is None:
        raise Exception("Database pool is not initialized")
    return db_module.pool

async def get_db_connection(pool: AsyncConnectionPool = Depends(get_db_pool)) -> AsyncConnection:
    async with pool.connection() as conn:
        yield conn

def get_redis_client() -> Redis:
    """FastAPI dependency — returns the shared Redis client."""
    return _get_redis()

# Repositories 

def get_schedule_repo(db: AsyncConnection = Depends(get_db_connection)) -> ScheduleRepository:
    return ScheduleRepository(db)

def get_schedule_service(repo: ScheduleRepository = Depends(get_schedule_repo)) -> ScheduleService:
    return ScheduleService(repo)

def get_shift_repo(db: AsyncConnection = Depends(get_db_connection)) -> ShiftRepository:
    return ShiftRepository(db)

def get_shift_service(repo: ShiftRepository = Depends(get_shift_repo)) -> ShiftService:
    return ShiftService(repo)

def get_handover_repo(db: AsyncConnection = Depends(get_db_connection)) -> HandoverRepository:
    return HandoverRepository(db)

def get_handover_service(repo: HandoverRepository = Depends(get_handover_repo)) -> HandoverService:
    return HandoverService(repo)

# Authentication 

async def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    conn: AsyncConnection = Depends(get_db_connection)
) -> dict:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header",
        )
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, role FROM schedule.employees WHERE id = %s", (x_user_id,))
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
            return {"id": str(row[0]), "role": row[1]}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

class RequireRoles:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {', '.join(self.allowed_roles)}"
            )
        return current_user
