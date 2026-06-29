from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


# columns of employee table

_EMPLOYEE_COLUMNS = """
    id, employee_code, first_name, last_name, gender, phone, email,
    password_hash, hire_date, role, department_id, position,
    default_shift_id, weekly_off_days, can_cover_night_shift,
    status, profile_image, remember_token, last_login,
    secondary_phone, secondary_email,
    can_create_tables, can_manage_help_docs,
    can_post_announcements, can_manage_fiberx_data,
    ui_preferences, created_at, updated_at, created_by
"""


class EmployeeRepository(BaseRepository):


    async def get_by_id(self, employee_id: UUID) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_EMPLOYEE_COLUMNS} FROM employees WHERE id = %s",
            (employee_id,),
        )

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_EMPLOYEE_COLUMNS} FROM employees WHERE email = %s",
            (email,),
        )

    async def get_by_code(self, code: str) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_EMPLOYEE_COLUMNS} FROM employees WHERE employee_code = %s",
            (code,),
        )

    # return multi-rows from employees tableq
    async def get_all(self) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_EMPLOYEE_COLUMNS} FROM employees ORDER BY first_name, last_name"
        )

    async def get_active(self) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"""SELECT {_EMPLOYEE_COLUMNS} FROM employees
                WHERE status = 'active'
                ORDER BY first_name, last_name"""
        )

    async def get_by_department(self, department_id: UUID) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"""SELECT {_EMPLOYEE_COLUMNS} FROM employees
                WHERE department_id = %s
                ORDER BY first_name, last_name""",
            (department_id,),
        )

    async def get_by_role(self, role: str) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"""SELECT {_EMPLOYEE_COLUMNS} FROM employees
                WHERE role = %s
                ORDER BY first_name, last_name""",
            (role,),
        )

    async def get_by_shift_id(self, shift_id: UUID) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"""SELECT {_EMPLOYEE_COLUMNS} FROM employees
                WHERE default_shift_id = %s
                ORDER BY first_name, last_name""",
            (shift_id,),
        )

    # insert into employees table and return the created employee with id and created_at and updated_at
    async def create(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO employees (
                employee_code, first_name, last_name, gender, phone, email,
                password_hash, hire_date, role, department_id, position,
                default_shift_id, weekly_off_days, can_cover_night_shift,
                status, profile_image, secondary_phone, secondary_email,
                can_create_tables, can_manage_help_docs,
                can_post_announcements, can_manage_fiberx_data,
                ui_preferences, created_by
            ) VALUES (
                %(employee_code)s, %(first_name)s, %(last_name)s, %(gender)s,
                %(phone)s, %(email)s, %(password_hash)s, %(hire_date)s,
                %(role)s, %(department_id)s, %(position)s,
                %(default_shift_id)s, %(weekly_off_days)s, %(can_cover_night_shift)s,
                %(status)s, %(profile_image)s, %(secondary_phone)s, %(secondary_email)s,
                %(can_create_tables)s, %(can_manage_help_docs)s,
                %(can_post_announcements)s, %(can_manage_fiberx_data)s,
                %(ui_preferences)s, %(created_by)s
            ) RETURNING id, created_at, updated_at""",
            data,
        )

    # update employee full data and return the number of updated rows
    async def update(self, employee_id: UUID, data: dict[str, Any]) -> int:
        data["id"] = employee_id
        return await self.execute(
            """UPDATE employees SET
                first_name = %(first_name)s,
                last_name = %(last_name)s,
                gender = %(gender)s,
                phone = %(phone)s,
                email = %(email)s,
                role = %(role)s,
                department_id = %(department_id)s,
                position = %(position)s,
                default_shift_id = %(default_shift_id)s,
                weekly_off_days = %(weekly_off_days)s,
                can_cover_night_shift = %(can_cover_night_shift)s,
                status = %(status)s,
                profile_image = %(profile_image)s,
                secondary_phone = %(secondary_phone)s,
                secondary_email = %(secondary_email)s,
                can_create_tables = %(can_create_tables)s,
                can_manage_help_docs = %(can_manage_help_docs)s,
                can_post_announcements = %(can_post_announcements)s,
                can_manage_fiberx_data = %(can_manage_fiberx_data)s,
                ui_preferences = %(ui_preferences)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(id)s""",
            data,
        )

    # update employee status and return the number of updated rows
    async def update_status(self, employee_id: UUID, status: str) -> int:
        return await self.execute(
            "UPDATE employees SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (status, employee_id),
        )

    async def update_password(self, employee_id: UUID, password_hash: str) -> int:
        return await self.execute(
            "UPDATE employees SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (password_hash, employee_id),
        )

    async def update_last_login(self, employee_id: UUID) -> int:
        return await self.execute(
            "UPDATE employees SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
            (employee_id,),
        )
    #update employee profile image and return the number of updated rows
    async def update_profile_image(self, employee_id: UUID, image_path: str) -> int:
        return await self.execute(
            "UPDATE employees SET profile_image = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (image_path, employee_id),
        )
    #update employee preferences and return the number of updated rows
    async def update_preferences(self, employee_id: UUID, prefs: dict) -> int:
        return await self.execute(
            """UPDATE employees
               SET ui_preferences = COALESCE(ui_preferences, '{}'::jsonb) || %s,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (prefs, employee_id),
        )

    #update employee help permission
    async def update_help_permission(self, employee_id: UUID, can_manage: bool) -> int:
        return await self.execute(
            "UPDATE employees SET can_manage_help_docs = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (can_manage, employee_id),
        )

    async def update_fiberx_permission(self, employee_id: UUID, can_manage: bool) -> int:
        return await self.execute(
            "UPDATE employees SET can_manage_fiberx_data = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (can_manage, employee_id),
        )

    async def update_announcement_permission(self, employee_id: UUID, can_post: bool) -> int:
        return await self.execute(
            "UPDATE employees SET can_post_announcements = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (can_post, employee_id),
        )

    async def update_table_permission(self, employee_id: UUID, can_create: bool) -> int:
        return await self.execute(
            "UPDATE employees SET can_create_tables = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (can_create, employee_id),
        )


    async def delete(self, employee_id: UUID) -> int:
        return await self.execute(
            "DELETE FROM employees WHERE id = %s",
            (employee_id,),
        )

    async def force_delete(self, employee_id: UUID) -> None:
        """Delete employee and clean up all foreign key references in a transaction."""
        cleanup_queries = [
            "DELETE FROM department_managers WHERE manager_id = %s",
            "UPDATE employees SET created_by = NULL WHERE created_by = %s",
            "UPDATE weekly_schedule SET published_by = NULL WHERE published_by = %s",
            "UPDATE weekly_schedule SET created_by = NULL WHERE created_by = %s",
            "UPDATE employee_shifts SET replaced_employee_id = NULL WHERE replaced_employee_id = %s",
            "UPDATE employee_shifts SET replacement_approved_by = NULL WHERE replacement_approved_by = %s",
            "UPDATE employee_shifts SET created_by = NULL WHERE created_by = %s",
            "UPDATE leaves SET approved_by_team_leader = NULL WHERE approved_by_team_leader = %s",
            "UPDATE leaves SET approved_by_manager = NULL WHERE approved_by_manager = %s",
            "UPDATE task_schedules SET created_by = NULL WHERE created_by = %s",
            "UPDATE task_assignments SET assigned_by = NULL WHERE assigned_by = %s",
            "UPDATE shift_swaps SET approved_by_team_leader = NULL WHERE approved_by_team_leader = %s",
            "UPDATE shift_swaps SET approved_by_manager = NULL WHERE approved_by_manager = %s",
            "DELETE FROM shift_swaps WHERE requester_id = %s OR target_employee_id = %s",
            "UPDATE notifications SET sender_id = NULL WHERE sender_id = %s",
            "UPDATE audit_logs SET employee_id = NULL WHERE employee_id = %s",
            "DELETE FROM employees WHERE id = %s",
        ]
        for query in cleanup_queries:
            # shift_swaps DELETE has two %s placeholders
            param_count = query.count("%s")
            params = (employee_id,) * param_count
            await self.execute(query, params)


    async def get_emails_by_department(self, department_id: UUID) -> list[str]:
        rows = await self.fetch_all(
            """SELECT email FROM employees
               WHERE department_id = %s AND status = 'active' AND email IS NOT NULL""",
            (department_id,),
        )
        return [r["email"] for r in rows if r["email"]]

    async def increment_failed_login(self, email: str) -> int | None:
        row = await self.execute_returning(
            """UPDATE employees
               SET failed_login_attempts = failed_login_attempts + 1
               WHERE email = %s
               RETURNING failed_login_attempts""",
            (email,),
        )
        return row["failed_login_attempts"] if row else None

    async def reset_failed_login(self, employee_id: UUID) -> int:
        return await self.execute(
            "UPDATE employees SET failed_login_attempts = 0 WHERE id = %s",
            (employee_id,),
        )
