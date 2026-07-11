import json
import structlog
from aio_pika.abc import AbstractIncomingMessage

from app.db.pool import pool
from app.repositories.audit_repo import AuditRepository
from app.repositories.notification_repo import NotificationRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

from shiftmaster_common.messaging.events import AuditLogEvent, NotificationEvent
from shiftmaster_common.messaging.rabbitmq import subscribe_to_event
from shiftmaster_common.cache.redis_client import check_idempotency

logger = structlog.get_logger(__name__)

async def handle_audit_log(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False, ignore_processed=True):
        try:
            payload = json.loads(message.body.decode("utf-8"))
            event = AuditLogEvent(**payload)

            logger.info("audit_log.consuming", event_id=str(event.event_id), action=event.action)

            if await check_idempotency(str(event.event_id)):
                return

            if not pool:
                raise RuntimeError("Database pool not initialized")

            async with pool.connection() as conn:
                repo = AuditRepository(conn)
                service = AuditService(repo)
                await service.create_from_event(event)

            logger.info("audit_log.processed", event_id=str(event.event_id))
        except Exception as e:
            logger.error("audit_log.failed", exc_info=e, message_id=message.message_id)
            await message.reject(requeue=False) # Will go to DLQ

async def handle_notification(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False, ignore_processed=True):
        try:
            payload = json.loads(message.body.decode("utf-8"))
            event = NotificationEvent(**payload)

            logger.info("notification.consuming", event_id=str(event.event_id), type=event.type)

            if await check_idempotency(str(event.event_id)):
                return

            if not pool:
                raise RuntimeError("Database pool not initialized")

            async with pool.connection() as conn:
                repo = NotificationRepository(conn)
                service = NotificationService(repo)
                await service.create_from_event(event)

            logger.info("notification.processed", event_id=str(event.event_id))
        except Exception as e:
            logger.error("notification.failed", exc_info=e, message_id=message.message_id)
            await message.reject(requeue=False)

async def start_consumers() -> None:
    logger.info("consumers.starting")
    # Using the shared library to subscribe dynamically
    await subscribe_to_event(
        routing_key="audit.log.created", 
        queue_name="notifications.audit_logs.queue", 
        handler=handle_audit_log
    )
    await subscribe_to_event(
        routing_key="notification.created", 
        queue_name="notifications.alerts.queue", 
        handler=handle_notification
    )
    logger.info("consumers.started")
