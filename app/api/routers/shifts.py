from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from uuid import UUID

from app.schemas.shift_schema import ShiftCreate, ShiftUpdate, ShiftResponse
from app.services.shift_service import ShiftService
from app.core.exceptions import NotFoundError, ConflictError
from app.api.deps import get_shift_service, get_current_user

router = APIRouter()

@router.get("/", response_model=List[ShiftResponse])
async def get_shifts(
    department_id: UUID | None = None,
    service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_all(department_id)

@router.post("/", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    shift_in: ShiftCreate,
    service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    try:
        return await service.create(shift_in.model_dump())
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: UUID,
    service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    try:
        return await service.get_by_id(shift_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: UUID,
    shift_in: ShiftUpdate,
    service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    try:
        return await service.update(shift_id, shift_in.model_dump(exclude_unset=True))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: UUID,
    service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user)
) -> None:
    try:
        await service.delete(shift_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
