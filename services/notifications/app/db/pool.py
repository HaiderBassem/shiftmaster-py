"""
Async PostgreSQL connection pool with retry logic.
"""

from __future__ import annotations

import tenacity
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings
from shiftmaster_common.logging.structured import get_logger

logger = get_logger(__name__)

pool: AsyncConnectionPool | None = None

_retry_on_pool_error = tenacity.retry(
    reraise=True,
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=16),
    before_sleep=lambda retry_state: logger.warning(
        "db.pool.retry",
        attempt=retry_state.attempt_number,
        wait_seconds=retry_state.next_action.sleep,  # type: ignore[union-attr]
    ),
)

@_retry_on_pool_error
async def create_pool() -> AsyncConnectionPool:
    global pool
    logger.info(
        "db.pool.opening",
        host=settings.db.host,
        port=settings.db.port,
        dbname=settings.db.name,
    )
    pool = AsyncConnectionPool(
        conninfo=settings.db.url,
        min_size=settings.db.min_conns,
        max_size=settings.db.max_open_conns,
        open=False,
        # Default schema for the notification service
        kwargs={"options": "-c search_path=notifications"}
    )
    await pool.open()
    await pool.check()
    logger.info("db.pool.ready")
    return pool

async def close_pool() -> None:
    global pool
    if pool:
        logger.info("db.pool.closing")
        await pool.close()
        pool = None
        logger.info("db.pool.closed")
