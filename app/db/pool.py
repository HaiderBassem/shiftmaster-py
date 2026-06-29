from psycopg_pool import AsyncConnectionPool
from app.core.config import settings


pool: AsyncConnectionPool | None = None


async def create_pool() -> AsyncConnectionPool:
    global pool
    pool = AsyncConnectionPool(
        conninfo=settings.db.url,
        min_size=settings.db.min_conns,
        max_size=settings.db.max_open_conns,
        open=False,
    )
    await pool.open()       
    await pool.check()      
    return pool


async def close_pool() -> None:
    global pool
    if pool:
        await pool.close()
        pool = None
