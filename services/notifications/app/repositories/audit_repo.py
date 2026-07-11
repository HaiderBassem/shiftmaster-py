from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository

_AUDIT_COLUMNS = """
    id, employee_id, action, table_name, record_id,
    old_data, new_data, ip_address, user_agent, created_at
"""

class AuditRepository(BaseRepository):

    async def create(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO audit_logs (
                employee_id, action, table_name, record_id,
                old_data, new_data, ip_address, user_agent
            ) VALUES (
                %(employee_id)s, %(action)s, %(table_name)s, %(record_id)s,
                %(old_data)s, %(new_data)s, %(ip_address)s, %(user_agent)s
            ) RETURNING id, created_at""",
            data,
        )

    async def get_by_table(self, table_name: str, limit: int = 50) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_AUDIT_COLUMNS} FROM audit_logs WHERE table_name = %s ORDER BY created_at DESC LIMIT %s",
            (table_name, limit),
        )

    async def get_by_employee(self, employee_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_AUDIT_COLUMNS} FROM audit_logs WHERE employee_id = %s ORDER BY created_at DESC LIMIT %s",
            (employee_id, limit),
        )

    async def get_by_record(self, table_name: str, record_id: UUID) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_AUDIT_COLUMNS} FROM audit_logs WHERE table_name = %s AND record_id = %s ORDER BY created_at DESC",
            (table_name, record_id),
        )
