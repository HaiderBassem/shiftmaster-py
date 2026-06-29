from __future__ import annotations
from typing import Self

from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


class BaseRepository:

    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn


    async def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> dict[str, Any] | None:

        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()


    async def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> list[dict[str, Any]]:

        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            return await cur.fetchall()


    async def execute(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> int:

        async with self._conn.cursor() as cur:
            await cur.execute(query, params)
            return cur.rowcount


    async def execute_returning(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> dict[str, Any] | None:


        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()


    async def fetch_scalar(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> Any:

        async with self._conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return row[0] if row else None
