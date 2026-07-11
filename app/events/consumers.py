"""
RabbitMQ consumers for processing background events.
"""
import asyncio
import json
import structlog
from aio_pika.abc import AbstractIncomingMessage

from app.events.schemas import AuditLogEvent, NotificationEvent
from app.events.broker import _channel, ROUTING_KEYS, DLX_NAME, EXCHANGE_NAME
from app.db.pool import pool
from app.core.redis import check_idempotency

logger = structlog.get_logger(__name__)


async def handle_audit_log(message: AbstractIncomingMessage) -> None:
    """Consume audit log events and insert them into the database."""
    async with message.process(requeue=False, ignore_processed=True):
        try:
            # Parse payload
            payload = json.loads(message.body.decode("utf-8"))
            event = AuditLogEvent(**payload)

            logger.info("audit_log.consuming", event_id=str(event.event_id), action=event.action)

            if await check_idempotency(str(event.event_id)):
                logger.info("audit_log.skipped_duplicate", event_id=str(event.event_id))
                return

            if not pool:
                raise RuntimeError("Database pool not initialized")

            async with pool.connection() as conn:
                # We can use event_id as the idempotency key if we had a dedicated table.
                # For this implementation, we just insert.
                await conn.execute(
                    """INSERT INTO audit_logs (
                        employee_id, action, table_name, record_id,
                        old_data, new_data, ip_address, user_agent
                    ) VALUES (
                        %(employee_id)s, %(action)s, %(table_name)s, %(record_id)s,
                        %(old_data)s, %(new_data)s, %(ip_address)s, %(user_agent)s
                    )""",
                    {
                        "employee_id": event.employee_id,
                        "action": event.action,
                        "table_name": event.table_name,
                        "record_id": event.record_id,
                        "old_data": json.dumps(event.old_data) if event.old_data else None,
                        "new_data": json.dumps(event.new_data) if event.new_data else None,
                        "ip_address": event.ip_address,
                        "user_agent": event.user_agent,
                    }
                )
            logger.info("audit_log.processed", event_id=str(event.event_id))
        except Exception as e:
            logger.error("audit_log.failed", exc_info=e, message_id=message.message_id)
            await message.reject(requeue=False) # Will go to DLQ


async def handle_notification(message: AbstractIncomingMessage) -> None:
    """Consume notification events and insert them into the database."""
    async with message.process(requeue=False, ignore_processed=True):
        try:
            payload = json.loads(message.body.decode("utf-8"))
            event = NotificationEvent(**payload)

            logger.info("notification.consuming", event_id=str(event.event_id), type=event.type)

            if await check_idempotency(str(event.event_id)):
                logger.info("notification.skipped_duplicate", event_id=str(event.event_id))
                return

            if not pool:
                raise RuntimeError("Database pool not initialized")

            async with pool.connection() as conn:
                await conn.execute(
                    """INSERT INTO notifications (
                        recipient_id, sender_id, title, message, type, reference_id, reference_type
                    ) VALUES (
                        %(recipient_id)s, %(sender_id)s, %(title)s, %(message)s, %(type)s, %(reference_id)s, %(reference_type)s
                    )""",
                    {
                        "recipient_id": event.recipient_id,
                        "sender_id": event.sender_id,
                        "title": event.title,
                        "message": event.message,
                        "type": event.type,
                        "reference_id": event.reference_id,
                        "reference_type": event.reference_type,
                    }
                )
            logger.info("notification.processed", event_id=str(event.event_id))
        except Exception as e:
            logger.error("notification.failed", exc_info=e, message_id=message.message_id)
            await message.reject(requeue=False)


async def start_consumers() -> None:
    """Start listening to RabbitMQ queues."""
    if not _channel:
        logger.warning("consumers.skipped", reason="RabbitMQ channel not initialized")
        return

    # Get queues
    audit_queue = await _channel.get_queue(ROUTING_KEYS["audit.log.created"])
    notification_queue = await _channel.get_queue(ROUTING_KEYS["notification.created"])

    # Start consuming
    await audit_queue.consume(handle_audit_log)
    await notification_queue.consume(handle_notification)
    
    logger.info("consumers.started")
