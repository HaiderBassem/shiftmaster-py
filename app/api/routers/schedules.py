from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from uuid import UUID
from datetime import date

from app.schemas.schedule_schema import (
    ScheduleTemplateResponse, ScheduleTemplateCreate,
    WeeklyScheduleCreate, WeeklyScheduleResponse,
    EmployeeShiftCreate, EmployeeShiftResponse, EmployeeShiftUpdate
)
from app.services.schedule_service import ScheduleService
from app.core.exceptions import NotFoundError
from app.api.deps import get_schedule_service, get_current_user

router = APIRouter()

# ── Templates ──
@router.get("/templates/employee/{employee_id}", response_model=List[ScheduleTemplateResponse])
async def get_templates(
    employee_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_templates_by_employee(employee_id)

@router.post("/templates", response_model=ScheduleTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_in: ScheduleTemplateCreate,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    # Example just taking the raw dict, in real scenario valid_from is managed
    data = template_in.model_dump()
    data["valid_from"] = "now()"
    data["valid_to"] = None
    try:
        return await service.create_template(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> None:
    try:
        await service.delete_template(template_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ── Employee Shifts ──
@router.get("/shifts", response_model=List[EmployeeShiftResponse])
async def get_shifts_by_date(
    shift_date: date,
    department_id: UUID | None = None,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_employee_shifts_by_date(shift_date, department_id)

@router.post("/shifts", response_model=EmployeeShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_employee_shift(
    shift_in: EmployeeShiftCreate,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    data = shift_in.model_dump()
    if not data.get("created_by"):
        data["created_by"] = current_user["id"]
    try:
        return await service.create_employee_shift(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/shifts/{shift_id}")
async def update_employee_shift(
    shift_id: UUID,
    shift_in: EmployeeShiftUpdate,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        await service.update_employee_shift(shift_id, shift_in.model_dump(exclude_unset=True))
        return {"success": True}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/shifts/{shift_id}/check-in")
async def check_in(
    shift_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        await service.check_in(shift_id)
        return {"success": True}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/shifts/{shift_id}/check-out")
async def check_out(
    shift_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        await service.check_out(shift_id)
        return {"success": True}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
