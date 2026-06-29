from typing import Any
from uuid import UUID

from app.repositories.employee_repo import EmployeeRepository
from app.core.exceptions import NotFoundError, ConflictError

class EmployeeService:
    def __init__(self, repo: EmployeeRepository):
        self.repo = repo

    async def get_by_id(self, employee_id: UUID) -> dict[str, Any]:
        emp = await self.repo.get_by_id(employee_id)
        if not emp:
            raise NotFoundError(f"Employee with ID {employee_id} not found")
        return emp

    async def get_by_email(self, email: str) -> dict[str, Any]:
        emp = await self.repo.get_by_email(email)
        if not emp:
            raise NotFoundError(f"Employee with email {email} not found")
        return emp

    async def get_by_code(self, code: str) -> dict[str, Any]:
        emp = await self.repo.get_by_code(code)
        if not emp:
            raise NotFoundError(f"Employee with code {code} not found")
        return emp

    async def get_all(self) -> list[dict[str, Any]]:
        return await self.repo.get_all()

    async def get_active(self) -> list[dict[str, Any]]:
        return await self.repo.get_active()

    async def get_by_department(self, department_id: UUID) -> list[dict[str, Any]]:
        return await self.repo.get_by_department(department_id)

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        # Validate uniqueness of email
        existing_email = await self.repo.get_by_email(data["email"])
        if existing_email:
            raise ConflictError(f"Email {data['email']} is already in use")

        # Validate uniqueness of employee_code if provided
        if data.get("employee_code"):
            existing_code = await self.repo.get_by_code(data["employee_code"])
            if existing_code:
                raise ConflictError(f"Employee code {data['employee_code']} is already in use")

        created = await self.repo.create(data)
        if not created:
            raise Exception("Failed to create employee")

        return await self.get_by_id(created["id"])

    async def update(self, employee_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        # Ensure exists and get current data
        existing = await self.get_by_id(employee_id)
        
        # If updating email, check for conflicts
        if "email" in data:
            existing_email = await self.repo.get_by_email(data["email"])
            if existing_email and existing_email["id"] != employee_id:
                raise ConflictError(f"Email {data['email']} is already in use by another account")

        # Merge the new data into the existing data since repo.update requires all fields
        updated_data = {**existing, **data}

        affected = await self.repo.update(employee_id, updated_data)
        if affected == 0:
            raise NotFoundError("Employee not found during update")

        return await self.get_by_id(employee_id)

    async def update_status(self, employee_id: UUID, status: str) -> None:
        affected = await self.repo.update_status(employee_id, status)
        if affected == 0:
            raise NotFoundError("Employee not found")

    async def update_password(self, employee_id: UUID, password_hash: str) -> None:
        affected = await self.repo.update_password(employee_id, password_hash)
        if affected == 0:
            raise NotFoundError("Employee not found")

    async def delete(self, employee_id: UUID, force: bool = False) -> None:
        # Validate existence
        await self.get_by_id(employee_id)
        
        if force:
            await self.repo.force_delete(employee_id)
        else:
            affected = await self.repo.delete(employee_id)
            if affected == 0:
                raise NotFoundError("Employee not found")

    async def get_emails_by_department(self, department_id: UUID) -> list[str]:
        return await self.repo.get_emails_by_department(department_id)
