from typing import Any
from uuid import UUID

from app.repositories.shift_repo import ShiftRepository
from app.core.exceptions import NotFoundError, ConflictError

class ShiftService:
    def __init__(self, repo: ShiftRepository):
        self.repo = repo

    async def get_by_id(self, shift_id: UUID) -> dict[str, Any]:
        shift = await self.repo.get_by_id(shift_id)
        if not shift:
            raise NotFoundError(f"Shift with ID {shift_id} not found")
        return shift

    async def get_by_code(self, code: str) -> dict[str, Any]:
        shift = await self.repo.get_by_code(code)
        if not shift:
            raise NotFoundError(f"Shift with code {code} not found")
        return shift

    async def get_all(self, department_id: UUID | None = None) -> list[dict[str, Any]]:
        return await self.repo.get_all(department_id)

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        # Ensure shift code is unique
        existing = await self.repo.get_by_code(data["shift_code"])
        if existing:
            raise ConflictError(f"Shift code {data['shift_code']} already exists")
            
        created = await self.repo.create(data)
        if not created:
            raise Exception("Failed to create shift")
            
        return await self.get_by_id(created["id"])

    async def update(self, shift_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        # Ensure it exists
        existing_shift = await self.get_by_id(shift_id)
        
        # If updating shift code, ensure it doesn't conflict with others
        if "shift_code" in data:
            existing = await self.repo.get_by_code(data["shift_code"])
            if existing and existing["id"] != shift_id:
                raise ConflictError(f"Shift code {data['shift_code']} is already in use")

        update_data = {**existing_shift, **data}
        affected = await self.repo.update(shift_id, update_data)
        if affected == 0:
            raise NotFoundError("Shift not found during update")
            
        return await self.get_by_id(shift_id)

    async def delete(self, shift_id: UUID) -> None:
        affected = await self.repo.delete(shift_id)
        if affected == 0:
            raise NotFoundError(f"Shift {shift_id} not found")
