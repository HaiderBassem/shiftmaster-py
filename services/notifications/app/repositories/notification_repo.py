from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository

_NOTIFICATION_COLUMNS = """
    id, recipient_id, sender_id, type, title, message,
    related_entity_type, related_entity_id, priority,
    is_read, read_at, action_url, created_at
"""

class NotificationRepository(BaseRepository):

    async def create(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO notifications (
                recipient_id, sender_id, type, title, message,
                related_entity_type, related_entity_id, priority, action_url
            ) VALUES (
                %(recipient_id)s, %(sender_id)s, %(type)s, %(title)s, %(message)s,
                %(related_entity_type)s, %(related_entity_id)s, %(priority)s, %(action_url)s
            ) RETURNING id, created_at""",
            data,
        )

    async def get_by_recipient(self, recipient_id: UUID, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_NOTIFICATION_COLUMNS} FROM notifications WHERE recipient_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (recipient_id, limit, offset),
        )

    async def mark_as_read(self, notification_id: UUID, recipient_id: UUID) -> bool:
        rowcount = await self.execute(
            "UPDATE notifications SET is_read = true, read_at = CURRENT_TIMESTAMP WHERE id = %s AND recipient_id = %s AND is_read = false",
            (notification_id, recipient_id)
        )
        return rowcount > 0

    async def mark_all_as_read(self, recipient_id: UUID) -> int:
        return await self.execute(
            "UPDATE notifications SET is_read = true, read_at = CURRENT_TIMESTAMP WHERE recipient_id = %s AND is_read = false",
            (recipient_id,)
        )
