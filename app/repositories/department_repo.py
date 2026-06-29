from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


# columns of departments table
_DEPARTMENT_COLUMNS = """
    id, department_code, name, description,
    COALESCE(fiberx_enabled, false) AS fiberx_enabled,
    max_leaves_per_day, active_modules,
    created_at, updated_at
"""


class DepartmentRepository(BaseRepository):

    # load manager UUIDs from junction table for a given department
    async def _load_manager_ids(self, department_id: UUID) -> list[str]:
        rows = await self.fetch_all(
            "SELECT manager_id FROM department_managers WHERE department_id = %s ORDER BY assigned_at",
            (department_id,),
        )
        return [str(r["manager_id"]) for r in rows]

    # attach manager_ids to a single department dict
    async def _with_managers(self, dept: dict[str, Any] | None) -> dict[str, Any] | None:
        if dept is None:
            return None
        dept["manager_ids"] = await self._load_manager_ids(dept["id"])
        return dept

    # attach manager_ids to a list of department dicts
    async def _with_managers_list(self, depts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for dept in depts:
            dept["manager_ids"] = await self._load_manager_ids(dept["id"])
        return depts


    async def get_by_id(self, department_id: UUID) -> dict[str, Any] | None:
        row = await self.fetch_one(
            f"SELECT {_DEPARTMENT_COLUMNS} FROM departments WHERE id = %s",
            (department_id,),
        )
        return await self._with_managers(row)

    async def get_by_code(self, code: str) -> dict[str, Any] | None:
        row = await self.fetch_one(
            f"SELECT {_DEPARTMENT_COLUMNS} FROM departments WHERE department_code = %s",
            (code,),
        )
        return await self._with_managers(row)

    async def get_all(self) -> list[dict[str, Any]]:
        rows = await self.fetch_all(
            f"SELECT {_DEPARTMENT_COLUMNS} FROM departments ORDER BY name"
        )
        return await self._with_managers_list(rows)

    # get all departments assigned to a specific manager
    async def get_by_manager_id(self, manager_id: UUID) -> list[dict[str, Any]]:
        rows = await self.fetch_all(
            f"""SELECT {_DEPARTMENT_COLUMNS}
                FROM departments d
                INNER JOIN department_managers dm ON dm.department_id = d.id
                WHERE dm.manager_id = %s
                ORDER BY d.name""",
            (manager_id,),
        )
        return await self._with_managers_list(rows)


    # insert new department and optionally assign managers
    async def create(self, data: dict[str, Any]) -> dict[str, Any] | None:
        row = await self.execute_returning(
            """INSERT INTO departments (department_code, name, description, max_leaves_per_day, active_modules)
               VALUES (%(department_code)s, %(name)s, %(description)s, %(max_leaves_per_day)s, %(active_modules)s)
               RETURNING id, created_at, updated_at""",
            data,
        )
        if row and data.get("manager_ids"):
            for mid in data["manager_ids"]:
                await self.add_manager(row["id"], mid)
        return row

    # update department info and optionally sync managers
    async def update(self, department_id: UUID, data: dict[str, Any]) -> int:
        data["id"] = department_id
        affected = await self.execute(
            """UPDATE departments SET
                name = %(name)s,
                description = %(description)s,
                max_leaves_per_day = %(max_leaves_per_day)s,
                active_modules = %(active_modules)s,
                updated_at = CURRENT_TIMESTAMP
               WHERE id = %(id)s""",
            data,
        )
        if "manager_ids" in data:
            await self.set_managers(department_id, data["manager_ids"])
        return affected

    async def delete(self, department_id: UUID) -> int:
        return await self.execute(
            "DELETE FROM departments WHERE id = %s",
            (department_id,),
        )


    # link a manager to a department (idempotent via ON CONFLICT)
    async def add_manager(self, department_id: UUID, manager_id: UUID) -> int:
        return await self.execute(
            """INSERT INTO department_managers (department_id, manager_id)
               VALUES (%s, %s) ON CONFLICT DO NOTHING""",
            (department_id, manager_id),
        )

    # unlink a manager from a department
    async def remove_manager(self, department_id: UUID, manager_id: UUID) -> int:
        return await self.execute(
            "DELETE FROM department_managers WHERE department_id = %s AND manager_id = %s",
            (department_id, manager_id),
        )

    # replace all managers for a department with the provided list
    async def set_managers(self, department_id: UUID, manager_ids: list[UUID]) -> None:
        await self.execute(
            "DELETE FROM department_managers WHERE department_id = %s",
            (department_id,),
        )
        for mid in manager_ids:
            await self.execute(
                "INSERT INTO department_managers (department_id, manager_id) VALUES (%s, %s)",
                (department_id, mid),
            )

    # get manager UUIDs for a department
    async def get_managers(self, department_id: UUID) -> list[str]:
        return await self._load_manager_ids(department_id)

    # toggle fiberx_enabled flag
    async def update_fiberx_enabled(self, department_id: UUID, enabled: bool) -> int:
        return await self.execute(
            "UPDATE departments SET fiberx_enabled = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (enabled, department_id),
        )
