from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from uuid import UUID
import json

from app.schemas.department_schema import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.services.department_service import DepartmentService
from shiftmaster_common.middleware.exceptions import AppException
from app.api.deps import get_department_service, get_current_user, RequireRoles

router = APIRouter()

@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    service: DepartmentService = Depends(get_department_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_all()

@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_in: DepartmentCreate,
    service: DepartmentService = Depends(get_department_service),
    current_user: dict = Depends(RequireRoles(["admin"]))
) -> Any:
    try:
        data = dept_in.model_dump()
        if data.get("active_modules") is not None:
            data["active_modules"] = json.dumps(data["active_modules"])
        return await service.create(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    service: DepartmentService = Depends(get_department_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    try:
        return await service.get_by_id(department_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    dept_in: DepartmentUpdate,
    service: DepartmentService = Depends(get_department_service),
    current_user: dict = Depends(RequireRoles(["admin"]))
) -> Any:
    try:
        data = dept_in.model_dump(exclude_unset=True)
        if "active_modules" in data and data["active_modules"] is not None:
            data["active_modules"] = json.dumps(data["active_modules"])
        return await service.update(department_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
