from collections.abc import AsyncGenerator
from psycopg import AsyncConnection
from app.db.pool import pool


async def get_connection() -> AsyncGenerator[AsyncConnection]:
    async with pool.connection() as conn:
        yield conn
