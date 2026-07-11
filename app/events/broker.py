"""
RabbitMQ message broker lifecycle, publisher, and consumer definitions using aio-pika.
Includes Dead-Letter Queue (DLQ) configuration and robust connection management.
"""

from __future__ import annotations

import json
from typing import Callable, Awaitable, Any
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
import structlog
from pydantic import BaseModel

from app.core.config import settings
from app.events.schemas import BaseEvent

logger = structlog.get_logger(__name__)

# Module-level connection and channel
_connection: AbstractRobustConnection | None = None
_channel: AbstractRobustChannel | None = None

# Exchange and Queue names
EXCHANGE_NAME = "shiftmaster.events"
DLX_NAME = "shiftmaster.events.dlx"
DLQ_NAME = "shiftmaster.dlq"

# Map routing keys to their respective queues
ROUTING_KEYS = {
    "audit.log.created": "audit.logs.queue",
    "notification.created": "notifications.queue",
}


async def init_rabbitmq() -> None:
    """Initialize RabbitMQ robust connection, channel, exchanges, and queues."""
    global _connection, _channel
    
    logger.info("rabbitmq.connecting", url=settings.rabbitmq.url.replace(settings.rabbitmq.password, "***"))
    try:
        _connection = await aio_pika.connect_robust(
            url=settings.rabbitmq.url,
            timeout=10
        )
        _channel = await _connection.channel()

        # Declare Dead-Letter Exchange (DLX) and Queue
        dlx = await _channel.declare_exchange(DLX_NAME, aio_pika.ExchangeType.FANOUT, durable=True)
        dlq = await _channel.declare_queue(DLQ_NAME, durable=True)
        await dlq.bind(dlx)

        # Declare Main Exchange
        exchange = await _channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)

        # Declare standard queues with DLX routing
        for routing_key, queue_name in ROUTING_KEYS.items():
            queue = await _channel.declare_queue(
                queue_name, 
                durable=True,
                arguments={
                    "x-dead-letter-exchange": DLX_NAME,
                    # Optional: x-message-ttl could be added here
                }
            )
            await queue.bind(exchange, routing_key)

        logger.info("rabbitmq.connected")
    except Exception as e:
        logger.error("rabbitmq.connection_failed", exc_info=e)
        raise


async def close_rabbitmq() -> None:
    """Gracefully close RabbitMQ connection."""
    global _connection, _channel
    if _connection and not _connection.is_closed:
        logger.info("rabbitmq.closing")
        await _connection.close()
        logger.info("rabbitmq.closed")
        _connection = None
        _channel = None


async def publish_event(routing_key: str, event: BaseEvent) -> None:
    """
    Publish a Pydantic event to the main exchange.
    Automatically includes correlation_id if not present.
    """
    if not _channel:
        logger.warning("rabbitmq.publish_skipped", reason="Channel not initialized", routing_key=routing_key)
        return

    exchange = await _channel.get_exchange(EXCHANGE_NAME)
    
    # Serialize event payload
    payload = event.model_dump_json().encode("utf-8")
    
    message = aio_pika.Message(
        body=payload,
        message_id=str(event.event_id),
        correlation_id=event.correlation_id,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json"
    )

    await exchange.publish(message, routing_key=routing_key)
    logger.debug("rabbitmq.published", routing_key=routing_key, event_id=str(event.event_id))

