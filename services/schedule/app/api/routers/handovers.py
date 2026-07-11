from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from uuid import UUID

from app.schemas.handover_schema import HandoverCreate, HandoverResponse, HandoverCommentBase
from app.services.handover_service import HandoverService
from app.core.exceptions import NotFoundError
from app.api.deps import get_handover_service, get_current_user

router = APIRouter()

@router.get("/department/{department_id}", response_model=List[HandoverResponse])
async def get_handovers_by_department(
    department_id: UUID,
    service: HandoverService = Depends(get_handover_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_by_department(department_id)

@router.post("/", response_model=HandoverResponse, status_code=status.HTTP_201_CREATED)
async def create_handover(
    handover_in: HandoverCreate,
    service: HandoverService = Depends(get_handover_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    data = handover_in.model_dump()
    data["creator_id"] = current_user["id"]
    try:
        return await service.create(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{handover_id}/claim", status_code=status.HTTP_200_OK)
async def claim_handover(
    handover_id: UUID,
    service: HandoverService = Depends(get_handover_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        await service.claim(handover_id, current_user["id"])
        return {"success": True, "message": "Handover claimed"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{handover_id}/complete", status_code=status.HTTP_200_OK)
async def complete_handover(
    handover_id: UUID,
    service: HandoverService = Depends(get_handover_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        await service.complete(handover_id, current_user["id"])
        return {"success": True, "message": "Handover completed"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{handover_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(
    handover_id: UUID,
    comment_in: HandoverCommentBase,
    service: HandoverService = Depends(get_handover_service),
    current_user: dict = Depends(get_current_user)
) -> dict:
    # Ensure they can only comment as themselves
    if comment_in.employee_id != current_user["id"] and current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Cannot comment as another user")
        
    try:
        await service.add_comment(handover_id, comment_in.employee_id, comment_in.comment)
        return {"success": True, "message": "Comment added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
