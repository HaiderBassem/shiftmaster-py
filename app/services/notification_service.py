import uuid
from typing import Optional
from uuid import UUID
from asgi_correlation_id import correlation_id

from app.events.broker import publish_event
from app.events.schemas import NotificationEvent

class NotificationService:
    async def send_notification(
        self,
        recipient_id: UUID,
        title: str,
        message: str,
        type: str,
        sender_id: Optional[UUID] = None,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None
    ) -> None:
        """
        Publish a notification event to RabbitMQ. 
        The background consumer will save it to the DB and handle actual delivery later.
        """
        event = NotificationEvent(
            event_id=uuid.uuid4(),
            correlation_id=correlation_id.get(),
            recipient_id=recipient_id,
            sender_id=sender_id,
            title=title,
            message=message,
            type=type,
            reference_id=reference_id,
            reference_type=reference_type
        )
        await publish_event("notification.created", event)
