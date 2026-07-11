import json
import logging
from aio_pika import IncomingMessage
from shiftmaster_common.messaging.rabbitmq import subscribe_to_event
from app.db.pool import pool

logger = logging.getLogger(__name__)

async def handle_employee_created(message: IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(f"Handling employee.created event for {data.get('id')}")
        
        try:
            async with pool.connection() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        INSERT INTO schedule.employees (id, first_name, last_name, email, department_id, role)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                            data["id"],
                            data["first_name"],
                            data["last_name"],
                            data["email"],
                            data.get("department_id"),
                            data.get("role", "employee")
                        )
                    )
        except Exception as e:
            logger.error(f"Error handling employee.created: {e}")

async def handle_employee_updated(message: IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(f"Handling employee.updated event for {data.get('id')}")
        
        try:
            async with pool.connection() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        UPDATE schedule.employees
                        SET first_name = %s,
                            last_name = %s,
                            email = %s,
                            department_id = %s,
                            role = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (
                            data["first_name"],
                            data["last_name"],
                            data["email"],
                            data.get("department_id"),
                            data.get("role", "employee"),
                            data["id"]
                        )
                    )
        except Exception as e:
            logger.error(f"Error handling employee.updated: {e}")

async def start_consumers():
    logger.info("Starting RabbitMQ consumers for Schedule Service")
    try:
        await subscribe_to_event("employee.created", "schedule_employee_created_queue", handle_employee_created)
        await subscribe_to_event("employee.updated", "schedule_employee_updated_queue", handle_employee_updated)
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumers: {e}")
