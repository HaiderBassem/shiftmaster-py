from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from uuid import UUID

from shiftmaster_common.middleware.exceptions import NotFoundError, ConflictError
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.services.employee_service import EmployeeService
from shiftmaster_common.security.jwt_utils import get_password_hash
from shiftmaster_common.middleware.exceptions import AppException
from app.api.deps import get_employee_service, get_current_user

router = APIRouter()

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    service: EmployeeService = Depends(get_employee_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_all()

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    emp_in: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    if current_user["role"] == "employee":
        raise HTTPException(status_code=403, detail="Employees cannot create users")
    if current_user["role"] == "manager" and emp_in.role not in ["team_leader", "employee"]:
        raise HTTPException(status_code=403, detail="Managers can only create Team Leaders or Employees")
    if current_user["role"] == "team_leader" and emp_in.role != "employee":
        raise HTTPException(status_code=403, detail="Team Leaders can only create Employees")

    # Hash password before saving
    data = emp_in.model_dump()
    data["password_hash"] = get_password_hash(data.pop("password"))
    data["created_by"] = current_user["id"]
    data.setdefault("status", "active")
    data.setdefault("profile_image", None)
    
    try:
        return await service.create(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    service: EmployeeService = Depends(get_employee_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    try:
        return await service.get_by_id(employee_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    emp_in: EmployeeUpdate,
    service: EmployeeService = Depends(get_employee_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    try:
        return await service.update(employee_id, emp_in.model_dump(exclude_unset=True))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: UUID,
    service: EmployeeService = Depends(get_employee_service),
    current_user: dict = Depends(get_current_user)
) -> None:
    try:
        await service.delete(employee_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
