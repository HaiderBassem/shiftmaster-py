from typing import Any
from uuid import UUID

from app.repositories.handover_repo import HandoverRepository
from app.core.exceptions import NotFoundError

class HandoverService:
    def __init__(self, repo: HandoverRepository):
        self.repo = repo

    async def get_by_department(self, department_id: UUID) -> list[dict[str, Any]]:
        return await self.repo.get_by_department(department_id)

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        created = await self.repo.create(data)
        if not created:
            raise Exception("Failed to create handover")
        return created

    async def claim(self, handover_id: UUID, employee_id: UUID) -> None:
        affected = await self.repo.claim(handover_id, employee_id)
        if affected == 0:
            raise NotFoundError("Handover not found or already claimed")

    async def unclaim(self, handover_id: UUID, employee_id: UUID) -> None:
        affected = await self.repo.unclaim(handover_id, employee_id)
        if affected == 0:
            raise NotFoundError("Handover not found or not claimed by this employee")

    async def complete(self, handover_id: UUID, employee_id: UUID) -> None:
        affected = await self.repo.complete(handover_id, employee_id)
        if affected == 0:
            raise NotFoundError("Handover not found")

    async def add_comment(self, handover_id: UUID, employee_id: UUID, comment: str) -> None:
        affected = await self.repo.add_comment(handover_id, employee_id, comment)
        if affected == 0:
            raise Exception("Failed to add comment")
