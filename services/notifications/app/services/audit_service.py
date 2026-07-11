import uuid
import json
from typing import Any
from uuid import UUID

from app.repositories.audit_repo import AuditRepository
from shiftmaster_common.messaging.events import AuditLogEvent

class AuditService:
    def __init__(self, repo: AuditRepository):
        self.repo = repo

    async def create_from_event(self, event: AuditLogEvent) -> None:
        old_data_json = json.dumps(event.old_data) if event.old_data else None
        new_data_json = json.dumps(event.new_data) if event.new_data else None
        
        await self.repo.create({
            "employee_id": event.employee_id,
            "action": event.action,
            "table_name": event.table_name,
            "record_id": event.record_id,
            "old_data": old_data_json,
            "new_data": new_data_json,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
        })

    async def get_by_table(self, table_name: str, limit: int = 50) -> list[dict[str, Any]]:
        return await self.repo.get_by_table(table_name, limit)

    async def get_by_employee(self, employee_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
        return await self.repo.get_by_employee(employee_id, limit)

    async def get_by_record(self, table_name: str, record_id: UUID) -> list[dict[str, Any]]:
        return await self.repo.get_by_record(table_name, record_id)
