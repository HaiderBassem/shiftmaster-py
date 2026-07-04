from typing import Any
from uuid import UUID

from app.repositories.audit_repo import AuditRepository

class AuditService:
    def __init__(self, repo: AuditRepository):
        self.repo = repo

    async def log_action(self, employee_id: UUID, action: str, table_name: str, record_id: UUID, old_data: dict | None = None, new_data: dict | None = None, ip_address: str | None = None, user_agent: str | None = None) -> None:

        data = {
            "employee_id": employee_id,
            "action": action,
            "table_name": table_name,
            "record_id": record_id,
            "old_data": old_data,
            "new_data": new_data,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        await self.repo.create(data)

    async def get_by_table(self, table_name: str, limit: int = 50) -> list[dict[str, Any]]:
        return await self.repo.get_by_table(table_name, limit)

    async def get_by_employee(self, employee_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
        return await self.repo.get_by_employee(employee_id, limit)

    async def get_by_record(self, table_name: str, record_id: UUID) -> list[dict[str, Any]]:
        return await self.repo.get_by_record(table_name, record_id)
