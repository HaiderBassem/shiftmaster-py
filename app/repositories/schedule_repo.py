from __future__ import annotations

from typing import Any
from uuid import UUID
from datetime import date, datetime

from app.repositories.base import BaseRepository

# ── Columns ─────────────────────────────────────────────────────────────

_TEMPLATE_COLUMNS = """
    id, employee_id, day_of_week, shift_id, is_off, valid_from, valid_to, created_at, updated_at
"""

_WEEKLY_SCHEDULE_COLUMNS = """
    id, week_start_date, week_end_date, template_id, status, published_by, published_at, notes, created_at
"""

_EMPLOYEE_SHIFT_COLUMNS = """
    id, schedule_id, employee_id, shift_id, shift_date, shift_status,
    leave_reason, is_replacement, replaced_employee_id, replacement_approved_by,
    check_in_time, check_out_time, actual_worked_hours, overtime_hours,
    created_at, updated_at, created_by
"""

class ScheduleRepository(BaseRepository):

    # ── Schedule Templates ──────────────────────────────────────────────

    async def get_templates_by_employee(self, employee_id: UUID) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_TEMPLATE_COLUMNS} FROM schedule_templates WHERE employee_id = %s ORDER BY day_of_week",
            (employee_id,),
        )

    async def create_template(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO schedule_templates (employee_id, day_of_week, shift_id, is_off, valid_from, valid_to)
               VALUES (%(employee_id)s, %(day_of_week)s, %(shift_id)s, %(is_off)s, %(valid_from)s, %(valid_to)s)
               RETURNING id, employee_id, day_of_week, shift_id, is_off, valid_from, valid_to, created_at, updated_at""",
            data,
        )

    async def update_template(self, template_id: UUID, data: dict[str, Any]) -> int:
        data["id"] = template_id
        return await self.execute(
            """UPDATE schedule_templates SET shift_id = %(shift_id)s, is_off = %(is_off)s,
                      valid_from = %(valid_from)s, valid_to = %(valid_to)s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %(id)s""",
            data,
        )

    async def delete_template(self, template_id: UUID) -> int:
        return await self.execute(
            "DELETE FROM schedule_templates WHERE id = %s",
            (template_id,),
        )

    # ── Weekly Schedules ────────────────────────────────────────────────

    async def get_weekly_schedule_by_date(self, week_start_date: date) -> dict[str, Any] | None:
        return await self.fetch_row(
            f"SELECT {_WEEKLY_SCHEDULE_COLUMNS} FROM weekly_schedule WHERE week_start_date = %s",
            (week_start_date,)
        )

    async def create_weekly_schedule(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            f"""INSERT INTO weekly_schedule (week_start_date, week_end_date, template_id, status, notes, created_by)
               VALUES (%(week_start_date)s, %(week_end_date)s, %(template_id)s, %(status)s, %(notes)s, %(created_by)s)
               RETURNING {_WEEKLY_SCHEDULE_COLUMNS}""",
            data,
        )

    async def upsert_template_for_day(self, employee_id: UUID, day_of_week: int, is_off: bool, shift_id: UUID | None) -> None:
        # Attempt update
        affected = await self.execute(
            """UPDATE schedule_templates
               SET is_off = %s, shift_id = %s, valid_to = NULL, updated_at = CURRENT_TIMESTAMP
               WHERE employee_id = %s AND day_of_week = %s""",
            (is_off, shift_id, employee_id, day_of_week),
        )
        if affected == 0:
            # Insert if no row existed
            await self.execute(
                """INSERT INTO schedule_templates (employee_id, day_of_week, shift_id, is_off, valid_from, valid_to)
                   VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, NULL)""",
                (employee_id, day_of_week, shift_id, is_off),
            )

    # ── Weekly Schedules ────────────────────────────────────────────────

    async def get_weekly_schedule(self, week_start: date) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"""SELECT {_WEEKLY_SCHEDULE_COLUMNS} FROM weekly_schedule
                WHERE week_start_date = %s::date
                ORDER BY created_at DESC LIMIT 1""",
            (week_start,),
        )

    async def get_weekly_schedule_by_id(self, schedule_id: UUID) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_WEEKLY_SCHEDULE_COLUMNS} FROM weekly_schedule WHERE id = %s",
            (schedule_id,),
        )

    async def create_weekly_schedule(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO weekly_schedule (week_start_date, week_end_date, template_id, status, published_by, notes)
               VALUES (%(week_start_date)s, %(week_end_date)s, %(template_id)s, %(status)s, %(published_by)s, %(notes)s)
               RETURNING id, week_start_date, week_end_date, template_id, status, published_by, notes, created_at""",
            data,
        )

    async def update_weekly_schedule_status(self, schedule_id: UUID, status: str, published_by: UUID | None) -> int:
        return await self.execute(
            """UPDATE weekly_schedule
               SET status = %s, published_by = %s, published_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (status, published_by, schedule_id),
        )

    # ── Employee Shifts ─────────────────────────────────────────────────

    async def get_employee_shifts_by_date(self, shift_date: date, department_id: UUID | None = None) -> list[dict[str, Any]]:
        query = f"""
            SELECT es.id, es.schedule_id, es.employee_id, es.shift_id, es.shift_date, es.shift_status,
                   es.leave_reason, es.is_replacement, es.replaced_employee_id, es.replacement_approved_by,
                   es.check_in_time, es.check_out_time, es.actual_worked_hours, es.overtime_hours,
                   es.created_at, es.updated_at, es.created_by
            FROM employee_shifts es
            JOIN employees e ON e.id = es.employee_id
            WHERE es.shift_date = %s
        """
        args: list[Any] = [shift_date]
        if department_id:
            query += " AND e.department_id = %s"
            args.append(department_id)
        query += " ORDER BY es.employee_id"
        return await self.fetch_all(query, args)

    async def get_employee_shifts_by_employee(self, employee_id: UUID, from_date: date, to_date: date) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_EMPLOYEE_SHIFT_COLUMNS} FROM employee_shifts WHERE employee_id = %s AND shift_date BETWEEN %s AND %s ORDER BY shift_date",
            (employee_id, from_date, to_date),
        )

    async def get_employee_shifts_in_range(self, from_date: date, to_date: date) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_EMPLOYEE_SHIFT_COLUMNS} FROM employee_shifts WHERE shift_date BETWEEN %s AND %s ORDER BY employee_id, shift_date",
            (from_date, to_date),
        )

    async def get_department_shifts_in_range(self, from_date: date, to_date: date, department_id: UUID) -> list[dict[str, Any]]:
        query = f"""
            SELECT es.id, es.schedule_id, es.employee_id, es.shift_id, es.shift_date, es.shift_status,
                   es.leave_reason, es.is_replacement, es.replaced_employee_id, es.replacement_approved_by,
                   es.check_in_time, es.check_out_time, es.actual_worked_hours, es.overtime_hours,
                   es.created_at, es.updated_at, es.created_by,
                   e.first_name, e.last_name, e.default_shift_id
            FROM employee_shifts es
            JOIN employees e ON e.id = es.employee_id
            WHERE es.shift_date BETWEEN %s AND %s
              AND e.department_id = %s
            ORDER BY e.first_name, e.last_name, es.shift_date
        """
        return await self.fetch_all(query, (from_date, to_date, department_id))

    async def get_employee_shift(self, employee_id: UUID, shift_date: date) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_EMPLOYEE_SHIFT_COLUMNS} FROM employee_shifts WHERE employee_id = %s AND shift_date = %s",
            (employee_id, shift_date),
        )

    async def get_employee_shift_by_id(self, shift_id: UUID) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_EMPLOYEE_SHIFT_COLUMNS} FROM employee_shifts WHERE id = %s",
            (shift_id,),
        )

    async def create_employee_shift(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO employee_shifts (
                   schedule_id, employee_id, shift_id, shift_date, shift_status,
                   leave_reason, is_replacement, replaced_employee_id, replacement_approved_by, created_by
               ) VALUES (
                   %(schedule_id)s, %(employee_id)s, %(shift_id)s, %(shift_date)s, %(shift_status)s,
                   %(leave_reason)s, %(is_replacement)s, %(replaced_employee_id)s, %(replacement_approved_by)s, %(created_by)s
               ) RETURNING id, schedule_id, employee_id, shift_id, shift_date, shift_status, leave_reason, is_replacement, replaced_employee_id, replacement_approved_by, created_by, check_in_time, check_out_time, actual_worked_hours, overtime_hours, created_at, updated_at""",
            data,
        )

    async def update_employee_shift(self, shift_id: UUID, data: dict[str, Any]) -> int:
        data["id"] = shift_id
        return await self.execute(
            """UPDATE employee_shifts SET
                   shift_id = %(shift_id)s, shift_status = %(shift_status)s, leave_reason = %(leave_reason)s,
                   is_replacement = %(is_replacement)s, replaced_employee_id = %(replaced_employee_id)s,
                   replacement_approved_by = %(replacement_approved_by)s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %(id)s""",
            data,
        )

    async def update_shift_status(self, shift_id: UUID, status: str, reason: str | None) -> int:
        return await self.execute(
            "UPDATE employee_shifts SET shift_status = %s, leave_reason = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (status, reason, shift_id),
        )

    async def assign_replacement(self, shift_id: UUID, replacement_employee_id: UUID, approved_by: UUID) -> int:
        return await self.execute(
            """UPDATE employee_shifts SET
                   is_replacement = true, replaced_employee_id = %s, replacement_approved_by = %s,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (replacement_employee_id, approved_by, shift_id),
        )

    async def check_in(self, shift_id: UUID) -> int:
        return await self.execute(
            "UPDATE employee_shifts SET check_in_time = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (shift_id,),
        )

    async def check_out(self, shift_id: UUID) -> int:
        return await self.execute(
            """UPDATE employee_shifts
               SET check_out_time = CURRENT_TIMESTAMP,
                   actual_worked_hours = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - check_in_time))/3600,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (shift_id,),
        )

    async def upsert_employee_shift(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO employee_shifts (
                   schedule_id, employee_id, shift_id, shift_date, shift_status, leave_reason, created_by
               ) VALUES (
                   %(schedule_id)s, %(employee_id)s, %(shift_id)s, %(shift_date)s, %(shift_status)s, %(leave_reason)s, %(created_by)s
               )
               ON CONFLICT (employee_id, shift_date)
               DO UPDATE SET
                   schedule_id = EXCLUDED.schedule_id,
                   shift_id = EXCLUDED.shift_id,
                   shift_status = EXCLUDED.shift_status,
                   leave_reason = EXCLUDED.leave_reason,
                   updated_at = CURRENT_TIMESTAMP
               RETURNING id, created_at, updated_at""",
            data,
        )

    async def delete_employee_shift(self, shift_id: UUID) -> int:
        return await self.execute(
            "DELETE FROM employee_shifts WHERE id = %s",
            (shift_id,),
        )

    # ── Smart Replacement / Eligibility ───────────────────────────────────────

    async def get_available_replacements(self, shift_date: date, department_id: UUID | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT e.id, e.employee_code, e.first_name, e.last_name, e.gender, e.phone, e.email,
                   e.hire_date, e.role, e.department_id, e.position, e.default_shift_id, e.weekly_off_days,
                   e.can_cover_night_shift, e.status, e.profile_image, e.last_login, e.secondary_phone, e.secondary_email,
                   e.created_at, e.updated_at, e.created_by
            FROM employees e
            JOIN employee_shifts es ON e.id = es.employee_id
            WHERE es.shift_date = %s - interval '1 day'
              AND es.shift_status IN ('off', 'leave', 'vacation')
              AND e.status = 'active'
              AND e.id NOT IN (
                  SELECT employee_id FROM employee_shifts
                  WHERE shift_date = %s AND shift_status = 'working'
              )
        """
        args: list[Any] = [shift_date, shift_date]
        if department_id:
            query += " AND e.department_id = %s"
            args.append(department_id)
        query += " ORDER BY e.first_name, e.last_name"
        return await self.fetch_all(query, args)

    async def get_eligible_assignees(self, shift_id: UUID, shift_date: date) -> list[dict[str, Any]]:
        query = """
            SELECT e.id, e.employee_code, e.first_name, e.last_name, e.gender, e.phone, e.email,
                   e.hire_date, e.role, e.department_id, e.position, e.default_shift_id, e.weekly_off_days,
                   e.can_cover_night_shift, e.status, e.profile_image, e.last_login, e.secondary_phone, e.secondary_email,
                   e.created_at, e.updated_at, e.created_by
            FROM employees e
            WHERE e.default_shift_id = %s
              AND e.status = 'active'
              AND e.role = 'employee'
              AND NOT EXISTS (
                  SELECT 1 FROM leaves lr
                  WHERE lr.employee_id = e.id
                    AND lr.status IN ('approved_by_manager', 'approved_by_team_leader')
                    AND %s::date BETWEEN lr.start_date AND lr.end_date
              )
              AND NOT EXISTS (
                  SELECT 1 FROM employee_shifts es
                  WHERE es.employee_id = e.id
                    AND es.shift_date = %s::date
                    AND es.shift_status IN ('off', 'leave', 'vacation')
              )
            ORDER BY e.first_name, e.last_name
        """
        return await self.fetch_all(query, (shift_id, shift_date, shift_date))

    async def get_swap_eligible_employees(self, department_id: UUID, exclude_employee_id: UUID, shift_date: date) -> list[dict[str, Any]]:
        query = """
            SELECT e.id, e.employee_code, e.first_name, e.last_name, e.gender, e.phone, e.email,
                   e.hire_date, e.role, e.department_id, e.position, e.default_shift_id, e.weekly_off_days,
                   e.can_cover_night_shift, e.status, e.profile_image, e.last_login, e.secondary_phone, e.secondary_email,
                   e.created_at, e.updated_at, e.created_by,
                   CASE WHEN es.shift_status IN ('off', 'leave', 'vacation') THEN true ELSE false END as is_off
            FROM employees e
            LEFT JOIN employee_shifts es ON e.id = es.employee_id AND es.shift_date = %s
            WHERE e.department_id = %s
              AND e.id != %s
              AND e.status = 'active'
            ORDER BY e.first_name, e.last_name
        """
        return await self.fetch_all(query, (shift_date, department_id, exclude_employee_id))

    async def get_shift_coverage_preview(self, shift_id: UUID, shift_date: date) -> dict[str, Any] | None:
        query = """
            SELECT
                COUNT(id) as total_assigned,
                SUM(CASE WHEN shift_status = 'working' THEN 1 ELSE 0 END) as total_working,
                SUM(CASE WHEN shift_status = 'off' THEN 1 ELSE 0 END) as total_off,
                SUM(CASE WHEN shift_status IN ('leave', 'vacation') THEN 1 ELSE 0 END) as total_on_leave
            FROM employee_shifts
            WHERE shift_date = %s AND shift_id = %s
        """
        row = await self.fetch_one(query, (shift_date, shift_id))
        if row:
            row["shift_id"] = shift_id
            row["shift_date"] = shift_date
            # Fix NULL SUMs to 0
            row["total_working"] = row["total_working"] or 0
            row["total_off"] = row["total_off"] or 0
            row["total_on_leave"] = row["total_on_leave"] or 0
        return row
