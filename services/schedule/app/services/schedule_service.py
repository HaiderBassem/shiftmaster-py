from typing import Any
from uuid import UUID
from datetime import date

from app.repositories.schedule_repo import ScheduleRepository
from app.core.exceptions import NotFoundError

class ScheduleService:
    def __init__(self, repo: ScheduleRepository):
        self.repo = repo

    async def get_templates_by_employee(self, employee_id: UUID) -> list[dict[str, Any]]:
        return await self.repo.get_templates_by_employee(employee_id)

    async def create_template(self, data: dict[str, Any]) -> dict[str, Any]:
        created = await self.repo.create_template(data)
        if not created:
            raise Exception("Failed to create template")
        return created

    async def delete_template(self, template_id: UUID) -> None:
        affected = await self.repo.delete_template(template_id)
        if affected == 0:
            raise NotFoundError("Schedule template not found")

    async def upsert_template_for_day(self, employee_id: UUID, day_of_week: int, is_off: bool, shift_id: UUID | None = None) -> None:
        await self.repo.upsert_template_for_day(employee_id, day_of_week, is_off, shift_id)

    # ── Weekly Schedules ──
    async def get_weekly_schedule(self, week_start: date) -> dict[str, Any]:
        ws = await self.repo.get_weekly_schedule(week_start)
        if not ws:
            raise NotFoundError(f"No weekly schedule found for week starting {week_start}")
        return ws

    async def create_weekly_schedule(self, data: dict[str, Any]) -> dict[str, Any]:
        created = await self.repo.create_weekly_schedule(data)
        if not created:
            raise Exception("Failed to create weekly schedule")
        return created

    # Employee Shifts 
    async def get_employee_shifts_by_date(self, shift_date: date, department_id: UUID | None = None) -> list[dict[str, Any]]:
        return await self.repo.get_employee_shifts_by_date(shift_date, department_id)

    async def get_employee_shift(self, employee_id: UUID, shift_date: date) -> dict[str, Any]:
        shift = await self.repo.get_employee_shift(employee_id, shift_date)
        if not shift:
            raise NotFoundError(f"No shift found for employee {employee_id} on {shift_date}")
        return shift

    async def create_employee_shift(self, data: dict[str, Any]) -> dict[str, Any]:
        created = await self.repo.create_employee_shift(data)
        if not created:
            raise Exception("Failed to create employee shift")
        return created

    async def update_employee_shift(self, shift_id: UUID, data: dict[str, Any]) -> None:
        affected = await self.repo.update_employee_shift(shift_id, data)
        if affected == 0:
            raise NotFoundError("Employee shift not found")

    async def update_shift_status(self, shift_id: UUID, status: str, reason: str | None = None) -> None:
        affected = await self.repo.update_shift_status(shift_id, status, reason)
        if affected == 0:
            raise NotFoundError("Employee shift not found")

    async def assign_replacement(self, shift_id: UUID, replacement_employee_id: UUID, approved_by: UUID) -> None:
        affected = await self.repo.assign_replacement(shift_id, replacement_employee_id, approved_by)
        if affected == 0:
            raise NotFoundError("Employee shift not found")

    async def check_in(self, shift_id: UUID) -> None:
        affected = await self.repo.check_in(shift_id)
        if affected == 0:
            raise NotFoundError("Employee shift not found")

    async def check_out(self, shift_id: UUID) -> None:
        affected = await self.repo.check_out(shift_id)
        if affected == 0:
            raise NotFoundError("Employee shift not found")

    # ── Eligibilities & Coverage ──
    async def get_available_replacements(self, shift_date: date, department_id: UUID | None = None) -> list[dict[str, Any]]:
        return await self.repo.get_available_replacements(shift_date, department_id)

    async def get_eligible_assignees(self, shift_id: UUID, shift_date: date) -> list[dict[str, Any]]:
        return await self.repo.get_eligible_assignees(shift_id, shift_date)

    async def get_shift_coverage_preview(self, shift_id: UUID, shift_date: date) -> dict[str, Any]:
        coverage = await self.repo.get_shift_coverage_preview(shift_id, shift_date)
        if not coverage:
            raise Exception("Could not generate coverage preview")
        return coverage
