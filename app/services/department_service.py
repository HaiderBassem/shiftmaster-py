from typing import Any
from uuid import UUID

from app.repositories.department_repo import DepartmentRepository
from app.core.exceptions import NotFoundError, ConflictError

class DepartmentService:
    def __init__(self, repo: DepartmentRepository):
        self.repo = repo

    async def get_by_id(self, department_id: UUID) -> dict[str, Any]:
        dept = await self.repo.get_by_id(department_id)
        if not dept:
            raise NotFoundError(f"Department with ID {department_id} not found")
        return dept

    async def get_by_code(self, code: str) -> dict[str, Any]:
        dept = await self.repo.get_by_code(code)
        if not dept:
            raise NotFoundError(f"Department with code {code} not found")
        return dept

    async def get_all(self) -> list[dict[str, Any]]:
        return await self.repo.get_all()

    async def get_by_manager_id(self, manager_id: UUID) -> list[dict[str, Any]]:
        return await self.repo.get_by_manager_id(manager_id)

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        # Check if code already exists
        existing = await self.repo.get_by_code(data["department_code"])
        if existing:
            raise ConflictError(f"Department code {data['department_code']} already exists")
            
        created = await self.repo.create(data)
        if not created:
            raise Exception("Failed to create department")
            
        # Return full object by reading it back
        return await self.get_by_id(created["id"])

    async def update(self, department_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        # Ensure it exists
        existing = await self.get_by_id(department_id)
        
        update_data = {**existing, **data}
        affected = await self.repo.update(department_id, update_data)
        if affected == 0:
            raise NotFoundError("Department not found during update")
            
        return await self.get_by_id(department_id)

    async def delete(self, department_id: UUID) -> None:
        affected = await self.repo.delete(department_id)
        if affected == 0:
            raise NotFoundError(f"Department {department_id} not found")

    # manager ops..

    async def add_manager(self, department_id: UUID, manager_id: UUID) -> None:
        await self.repo.add_manager(department_id, manager_id)

    async def remove_manager(self, department_id: UUID, manager_id: UUID) -> None:
        await self.repo.remove_manager(department_id, manager_id)

    async def set_managers(self, department_id: UUID, manager_ids: list[UUID]) -> None:
        await self.repo.set_managers(department_id, manager_ids)

    async def update_fiberx_enabled(self, department_id: UUID, enabled: bool) -> None:
        await self.repo.update_fiberx_enabled(department_id, enabled)
