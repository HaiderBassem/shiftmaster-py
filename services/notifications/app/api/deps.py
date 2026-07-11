from fastapi import Depends
from psycopg import AsyncConnection
from app.db.pool import pool
from app.repositories.audit_repo import AuditRepository
from app.repositories.notification_repo import NotificationRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

async def get_db_connection():
    if not pool:
        raise RuntimeError("Database pool not initialized")
    async with pool.connection() as conn:
        yield conn

async def get_audit_service(conn: AsyncConnection = Depends(get_db_connection)) -> AuditService:
    repo = AuditRepository(conn)
    return AuditService(repo)

async def get_notification_service(conn: AsyncConnection = Depends(get_db_connection)) -> NotificationService:
    repo = NotificationRepository(conn)
    return NotificationService(repo)
