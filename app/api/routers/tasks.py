from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from uuid import UUID
from datetime import date

from app.schemas.task_schema import (
    TaskScheduleCreate, TaskScheduleUpdate, TaskScheduleResponse,
    TaskAssignmentCreate, TaskAssignmentResponse,
    TaskExecutionResponse
)
from app.services.task_service import TaskService
from app.core.exceptions import NotFoundError
from app.api.deps import get_task_service, get_current_user, RequireRoles

router = APIRouter()

@router.get("/schedules", response_model=List[TaskScheduleResponse])
async def get_active_schedules(
    department_id: UUID | None = None,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_active_schedules(department_id)

@router.post("/schedules", response_model=TaskScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_in: TaskScheduleCreate,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(RequireRoles(["admin", "manager", "team_leader"]))
) -> Any:
    data = schedule_in.model_dump()
    data["created_by"] = current_user["id"]
    try:
        return await service.create_schedule(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/schedules/{schedule_id}", response_model=TaskScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    try:
        return await service.get_schedule(schedule_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/schedules/{schedule_id}", response_model=TaskScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    schedule_in: TaskScheduleUpdate,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(RequireRoles(["admin", "manager", "team_leader"]))
) -> Any:
    try:
        return await service.update_schedule(schedule_id, schedule_in.model_dump(exclude_unset=True))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(RequireRoles(["admin", "manager", "team_leader"]))
) -> None:
    try:
        await service.delete_schedule(schedule_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/boards/{board_id}/view")
async def get_board_view(
    board_id: UUID,
    shift_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(get_current_user)
) -> list[dict[str, Any]]:
    return await service.get_board_view(board_id, shift_id, from_date, to_date)

@router.post("/executions/{execution_id}/start")
async def start_execution(
    execution_id: UUID,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    # Check if assigned to current user
    assigned_emp_id = await service.repo.fetch_scalar(
        "SELECT ta.employee_id FROM task_assignments ta JOIN task_executions te ON te.assignment_id = ta.id WHERE te.id = %s",
        (execution_id,)
    )
    if assigned_emp_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only start tasks assigned to you")

    try:
        await service.start_execution(execution_id)
        return {"success": True}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/executions/{execution_id}/complete")
async def complete_execution(
    execution_id: UUID,
    completion_type: str,
    notes: str | None = None,
    service: TaskService = Depends(get_task_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    # Check if assigned to current user
    assigned_emp_id = await service.repo.fetch_scalar(
        "SELECT ta.employee_id FROM task_assignments ta JOIN task_executions te ON te.assignment_id = ta.id WHERE te.id = %s",
        (execution_id,)
    )
    if assigned_emp_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only complete tasks assigned to you")

    try:
        await service.complete_execution(execution_id, completion_type, notes)
        return {"success": True}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
