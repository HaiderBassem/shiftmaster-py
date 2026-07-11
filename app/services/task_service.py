from typing import Any
from uuid import UUID
from datetime import date

from app.repositories.task_repo import TaskRepository
from app.core.exceptions import NotFoundError

class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    # ── Schedules ──
    async def get_schedule(self, schedule_id: UUID) -> dict[str, Any]:
        schedule = await self.repo.get_schedule_by_id(schedule_id)
        if not schedule:
            raise NotFoundError("Task schedule not found")
        return schedule

    async def get_active_schedules(self, department_id: UUID | None = None) -> list[dict[str, Any]]:
        return await self.repo.get_active_schedules(department_id)

    async def create_schedule(self, data: dict[str, Any]) -> dict[str, Any]:
        created = await self.repo.create_schedule(data)
        if not created:
            raise Exception("Failed to create task schedule")
        return await self.get_schedule(created["id"])

    async def update_schedule(self, schedule_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        affected = await self.repo.update_schedule(schedule_id, data)
        if affected == 0:
            raise NotFoundError("Task schedule not found")
        return await self.get_schedule(schedule_id)

    async def toggle_schedule_active(self, schedule_id: UUID, is_active: bool) -> None:
        affected = await self.repo.toggle_schedule_active(schedule_id, is_active)
        if affected == 0:
            raise NotFoundError("Task schedule not found")

    async def delete_schedule(self, schedule_id: UUID) -> None:
        affected = await self.repo.delete_schedule(schedule_id)
        if affected == 0:
            raise NotFoundError("Task schedule not found")

    # ── Boards ──
    async def get_board_view(self, board_id: UUID, shift_id: UUID | None = None, from_date: date | None = None, to_date: date | None = None) -> list[dict[str, Any]]:
        return await self.repo.get_board_view(board_id, shift_id, from_date, to_date)

    async def get_board_stats(self, department_id: UUID | None = None) -> list[dict[str, Any]]:
        return await self.repo.get_board_stats(department_id)

    async def get_board_eligible_employees(self, shift_id: UUID | None = None, target_date: date | None = None, department_id: UUID | None = None) -> list[dict[str, Any]]:
        return await self.repo.get_board_eligible_employees(shift_id, target_date, department_id)

    # ── Employee View ──
    async def get_my_weekly_tasks(self, employee_id: UUID, week_start: date, week_end: date) -> list[dict[str, Any]]:
        return await self.repo.get_my_weekly_tasks(employee_id, week_start, week_end)

    # ── Assignments ──
    async def create_assignment(self, data: dict[str, Any]) -> dict[str, Any]:
        created = await self.repo.create_assignment(data)
        if not created:
            raise Exception("Failed to create task assignment")
        return created

    async def delete_assignment(self, assignment_id: UUID) -> None:
        await self.repo.delete_assignment(assignment_id)

    # ── Executions ──

    async def get_execution_assigned_employee_id(self, execution_id: UUID) -> UUID | None:
        """
        Return the UUID of the employee assigned to *execution_id*, or None
        if the execution doesn't exist.  Used for authorisation in routers.
        """
        row = await self.repo.get_execution_assigned_employee(execution_id)
        return row["employee_id"] if row else None

    async def start_execution(self, execution_id: UUID) -> None:
        affected = await self.repo.start_execution(execution_id)
        if affected == 0:
            raise NotFoundError("Task execution not found")

    async def complete_execution(self, execution_id: UUID, completion_type: str, notes: str | None = None) -> None:
        affected = await self.repo.complete_execution(execution_id, completion_type, notes)
        if affected == 0:
            raise NotFoundError("Task execution not found")

    # ── Recurring ──
    async def materialize_recurring_tasks(self, board_id: UUID, from_date: date, to_date: date) -> None:
        await self.repo.materialize_recurring_for_date_range(board_id, from_date, to_date)
