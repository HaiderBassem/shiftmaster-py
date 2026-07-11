from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from uuid import UUID

from app.services.notification_service import NotificationService
from app.api.deps import get_notification_service

router = APIRouter()

@router.get("/recipient/{recipient_id}")
async def get_notifications(
    recipient_id: UUID,
    limit: int = 50,
    offset: int = 0,
    service: NotificationService = Depends(get_notification_service)
) -> Any:
    return await service.get_by_recipient(recipient_id, limit, offset)

@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    recipient_id: UUID,
    service: NotificationService = Depends(get_notification_service)
) -> Any:
    success = await service.mark_as_read(notification_id, recipient_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found or already read")
    return {"status": "success"}

@router.post("/recipient/{recipient_id}/read-all")
async def mark_all_as_read(
    recipient_id: UUID,
    service: NotificationService = Depends(get_notification_service)
) -> Any:
    count = await service.mark_all_as_read(recipient_id)
    return {"status": "success", "updated_count": count}
