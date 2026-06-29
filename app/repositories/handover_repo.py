from __future__ import annotations

from typing import Any
from uuid import UUID
import json

from app.repositories.base import BaseRepository

class HandoverRepository(BaseRepository):

    async def create(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO shift_handovers (
                department_id, creator_id, shift_summary, pending_issues, status
            ) VALUES (
                %(department_id)s, %(creator_id)s, %(shift_summary)s, %(pending_issues)s, 'open'
            ) RETURNING id, created_at, updated_at""",
            data,
        )

    async def get_by_department(self, department_id: UUID) -> list[dict[str, Any]]:
        query = """
            SELECT h.id, h.department_id, h.creator_id, h.shift_summary, h.pending_issues, h.status, h.claimed_by, h.done_by, h.created_at, h.updated_at,
                   c.first_name || ' ' || c.last_name as creator_name,
                   cl.first_name || ' ' || cl.last_name as claimer_name,
                   d.first_name || ' ' || d.last_name as done_by_name,
                   COALESCE(
                       (
                           SELECT json_agg(json_build_object(
                               'id', hc.id,
                               'employee_id', hc.employee_id,
                               'author_name', e.first_name || ' ' || e.last_name,
                               'comment', hc.comment,
                               'created_at', hc.created_at
                           ) ORDER BY hc.created_at ASC)
                           FROM handover_comments hc
                           JOIN employees e ON e.id = hc.employee_id
                           WHERE hc.handover_id = h.id
                       ), '[]'::json
                   ) as comments
            FROM shift_handovers h
            JOIN employees c ON c.id = h.creator_id
            LEFT JOIN employees cl ON cl.id = h.claimed_by
            LEFT JOIN employees d ON d.id = h.done_by
            WHERE h.department_id = %s
            ORDER BY h.created_at DESC
        """
        rows = await self.fetch_all(query, (department_id,))
        for row in rows:
            # Parse comments JSON returned by PostgreSQL json_agg
            if isinstance(row.get("comments"), str):
                try:
                    row["comments"] = json.loads(row["comments"])
                except json.JSONDecodeError:
                    row["comments"] = []
            elif row.get("comments") is None:
                row["comments"] = []
        return rows

    async def claim(self, handover_id: UUID, employee_id: UUID) -> int:
        return await self.execute(
            """UPDATE shift_handovers
               SET status = 'claimed', claimed_by = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s AND status = 'open'""",
            (employee_id, handover_id),
        )

    async def unclaim(self, handover_id: UUID, employee_id: UUID) -> int:
        return await self.execute(
            """UPDATE shift_handovers
               SET status = 'open', claimed_by = NULL, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s AND claimed_by = %s AND status = 'claimed'""",
            (handover_id, employee_id),
        )

    async def add_comment(self, handover_id: UUID, employee_id: UUID, comment: str) -> int:
        affected = await self.execute(
            "INSERT INTO handover_comments (handover_id, employee_id, comment) VALUES (%s, %s, %s)",
            (handover_id, employee_id, comment),
        )
        if affected > 0:
            await self.execute(
                "UPDATE shift_handovers SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (handover_id,),
            )
        return affected

    async def complete(self, handover_id: UUID, employee_id: UUID) -> int:
        return await self.execute(
            """UPDATE shift_handovers
               SET status = 'completed', done_by = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (employee_id, handover_id),
        )
