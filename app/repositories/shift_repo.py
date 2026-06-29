from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


# columns of shifts table
_SHIFT_COLUMNS = """
    id, shift_code, name, name_en, start_time, end_time, color_code,
    requires_vehicle, min_rest_hours, department_id, created_at
"""


class ShiftRepository(BaseRepository):

    async def get_by_id(self, shift_id: UUID) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_SHIFT_COLUMNS} FROM shifts WHERE id = %s",
            (shift_id,),
        )

    async def get_by_code(self, code: str) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_SHIFT_COLUMNS} FROM shifts WHERE shift_code = %s",
            (code,),
        )

    # if department_id is None, return all shifts (global + department-specific)
    async def get_all(self, department_id: UUID | None = None) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"""SELECT {_SHIFT_COLUMNS} FROM shifts
                WHERE (%s::uuid IS NULL OR department_id = %s OR department_id IS NULL)
                ORDER BY start_time""",
            (str(department_id) if department_id else None,
             str(department_id) if department_id else None),
        )

    # insert new shift and return id + created_at
    async def create(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO shifts (
                shift_code, name, name_en, start_time, end_time, color_code,
                requires_vehicle, min_rest_hours, department_id
            ) VALUES (
                %(shift_code)s, %(name)s, %(name_en)s, %(start_time)s, %(end_time)s,
                %(color_code)s, %(requires_vehicle)s, %(min_rest_hours)s, %(department_id)s
            ) RETURNING id, created_at""",
            data,
        )

    # update shift full data
    async def update(self, shift_id: UUID, data: dict[str, Any]) -> int:
        data["id"] = shift_id
        return await self.execute(
            """UPDATE shifts SET
                shift_code = %(shift_code)s,
                name = %(name)s,
                name_en = %(name_en)s,
                start_time = %(start_time)s,
                end_time = %(end_time)s,
                color_code = %(color_code)s,
                requires_vehicle = %(requires_vehicle)s,
                min_rest_hours = %(min_rest_hours)s,
                department_id = %(department_id)s
            WHERE id = %(id)s""",
            data,
        )

    async def delete(self, shift_id: UUID) -> int:
        return await self.execute(
            "DELETE FROM shifts WHERE id = %s",
            (shift_id,),
        )
