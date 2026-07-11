"""
Async PostgreSQL connection pool with retry logic.

Uses psycopg3's AsyncConnectionPool wrapped with tenacity retry/backoff
so that transient Postgres hiccups (e.g. during container restarts) don't
immediately crash the application.

The global `pool` variable is managed by the FastAPI lifespan; never
instantiate it directly elsewhere.
"""

from __future__ import annotations

import tenacity
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings
from shiftmaster_common.logging.structured import get_logger

logger = get_logger(__name__)

pool: AsyncConnectionPool | None = None


# ── Retry configuration ───────────────────────────────────────────────────────
# Retries up to 5 times with exponential backoff: 1s, 2s, 4s, 8s, 16s
# Total wait ceiling: ~30 s — enough for Postgres to finish initialising.

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


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@_retry_on_pool_error
async def create_pool() -> AsyncConnectionPool:
    """
    Open and validate the connection pool.

    Retries up to 5× with exponential backoff on connection errors.
    Raises the last exception if all retries are exhausted.
    """
    global pool
    logger.info(
        "db.pool.opening",
        host=settings.db.host,
        port=settings.db.port,
        dbname=settings.db.name,
        min_size=settings.db.min_conns,
        max_size=settings.db.max_open_conns,
    )
    pool = AsyncConnectionPool(
        conninfo=settings.db.url,
        min_size=settings.db.min_conns,
        max_size=settings.db.max_open_conns,
        open=False,
    )
    await pool.open()
    await pool.check()
    logger.info("db.pool.ready")
    return pool


async def close_pool() -> None:
    """Gracefully drain and close the connection pool."""
    global pool
    if pool:
        logger.info("db.pool.closing")
        await pool.close()
        pool = None
        logger.info("db.pool.closed")
