from typing import Any
from uuid import UUID

from app.repositories.notification_repo import NotificationRepository
from shiftmaster_common.messaging.events import NotificationEvent

class NotificationService:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def create_from_event(self, event: NotificationEvent) -> None:
        await self.repo.create({
            "recipient_id": event.recipient_id,
            "sender_id": event.sender_id,
            "type": event.type,
            "title": event.title,
            "message": event.message,
            "related_entity_type": event.reference_type,
            "related_entity_id": event.reference_id,
            "priority": getattr(event, "priority", "medium"), # Not in event schema yet, default to medium
            "action_url": getattr(event, "action_url", None)
        })

    async def get_by_recipient(self, recipient_id: UUID, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return await self.repo.get_by_recipient(recipient_id, limit, offset)

    async def mark_as_read(self, notification_id: UUID, recipient_id: UUID) -> bool:
        return await self.repo.mark_as_read(notification_id, recipient_id)

    async def mark_all_as_read(self, recipient_id: UUID) -> int:
        return await self.repo.mark_all_as_read(recipient_id)
