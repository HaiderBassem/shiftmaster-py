import uuid
from typing import Any
from uuid import UUID
from asgi_correlation_id import correlation_id

from app.repositories.audit_repo import AuditRepository
from app.events.broker import publish_event
from app.events.schemas import AuditLogEvent

class AuditService:
    def __init__(self, repo: AuditRepository):
        self.repo = repo

    async def log_action(self, employee_id: UUID, action: str, table_name: str, record_id: UUID, old_data: dict | None = None, new_data: dict | None = None, ip_address: str | None = None, user_agent: str | None = None) -> None:

        event = AuditLogEvent(
            event_id=uuid.uuid4(),
            correlation_id=correlation_id.get(),
            employee_id=employee_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        await publish_event("audit.log.created", event)

    async def get_by_table(self, table_name: str, limit: int = 50) -> list[dict[str, Any]]:
        return await self.repo.get_by_table(table_name, limit)

    async def get_by_employee(self, employee_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
        return await self.repo.get_by_employee(employee_id, limit)

    async def get_by_record(self, table_name: str, record_id: UUID) -> list[dict[str, Any]]:
        return await self.repo.get_by_record(table_name, record_id)
