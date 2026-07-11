from __future__ import annotations

from typing import Any
from uuid import UUID
from datetime import date, datetime

from app.repositories.base import BaseRepository

_SCHEDULE_COLUMNS = """
    id, title, description, schedule_type, board_id, shift_id, recurrence, recurrence_days,
    max_assignees, is_active, created_by, created_at, updated_at
"""

class TaskRepository(BaseRepository):

    # ── Task Schedules ────────────────────────────────────────────────────────

    async def get_schedule_by_id(self, schedule_id: UUID) -> dict[str, Any] | None:
        return await self.fetch_one(
            f"SELECT {_SCHEDULE_COLUMNS} FROM task_schedules WHERE id = %s",
            (schedule_id,),
        )

    async def get_schedules_by_type(self, schedule_type: str) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_SCHEDULE_COLUMNS} FROM task_schedules WHERE schedule_type = %s AND is_active = true ORDER BY title",
            (schedule_type,),
        )

    async def get_schedules_by_shift(self, shift_id: UUID) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_SCHEDULE_COLUMNS} FROM task_schedules WHERE shift_id = %s AND is_active = true ORDER BY title",
            (shift_id,),
        )

    async def get_schedules_by_board(self, board_id: UUID) -> list[dict[str, Any]]:
        return await self.fetch_all(
            f"SELECT {_SCHEDULE_COLUMNS} FROM task_schedules WHERE board_id = %s AND is_active = true ORDER BY title",
            (board_id,),
        )

    async def get_active_schedules(self, department_id: UUID | None = None) -> list[dict[str, Any]]:
        query = f"""
            SELECT ts.* FROM task_schedules ts
            LEFT JOIN task_boards tb ON tb.id = ts.board_id
            WHERE ts.is_active = true AND (%s::uuid IS NULL OR tb.department_id = %s)
            ORDER BY ts.schedule_type, ts.title
        """
        return await self.fetch_all(query, (department_id, department_id))

    async def get_all_schedules(self, department_id: UUID | None = None) -> list[dict[str, Any]]:
        query = f"""
            SELECT ts.* FROM task_schedules ts
            LEFT JOIN task_boards tb ON tb.id = ts.board_id
            WHERE (%s::uuid IS NULL OR tb.department_id = %s)
            ORDER BY ts.schedule_type, ts.title
        """
        return await self.fetch_all(query, (department_id, department_id))

    async def create_schedule(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO task_schedules (
                   title, description, schedule_type, board_id, shift_id, recurrence,
                   recurrence_days, max_assignees, is_active, created_by
               ) VALUES (
                   %(title)s, %(description)s, %(schedule_type)s, %(board_id)s, %(shift_id)s, %(recurrence)s,
                   %(recurrence_days)s, %(max_assignees)s, %(is_active)s, %(created_by)s
               ) RETURNING id, title, description, schedule_type, board_id, shift_id, recurrence, recurrence_days, max_assignees, is_active, created_by, created_at, updated_at""",
            data,
        )

    async def update_schedule(self, schedule_id: UUID, data: dict[str, Any]) -> int:
        data["id"] = schedule_id
        return await self.execute(
            """UPDATE task_schedules SET
                   title = %(title)s, description = %(description)s, schedule_type = %(schedule_type)s,
                   board_id = %(board_id)s, shift_id = %(shift_id)s, recurrence = %(recurrence)s,
                   recurrence_days = %(recurrence_days)s, max_assignees = %(max_assignees)s,
                   is_active = %(is_active)s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %(id)s""",
            data,
        )

    async def toggle_schedule_active(self, schedule_id: UUID, is_active: bool) -> int:
        return await self.execute(
            "UPDATE task_schedules SET is_active = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (is_active, schedule_id),
        )

    async def delete_schedule(self, schedule_id: UUID) -> int:
        return await self.execute(
            "DELETE FROM task_schedules WHERE id = %s",
            (schedule_id,),
        )

    # ── Board View & Tracker ──────────────────────────────────────────────────

    async def get_board_view(self, board_id: UUID, shift_id: UUID | None = None, from_date: date | None = None, to_date: date | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT
                e.id AS employee_id,
                e.first_name || ' ' || e.last_name AS employee_name,
                e.employee_code,
                EXTRACT(DOW FROM ta.assigned_date)::int AS day_of_week,
                ta.assigned_date,
                ts.id AS task_id,
                ts.title AS task_title,
                ta.id AS assignment_id,
                te.id AS execution_id,
                COALESCE(te.status, 'pending') AS status,
                te.started_at,
                te.completed_at
            FROM task_schedules ts
            JOIN task_assignments ta ON ta.schedule_id = ts.id
            JOIN employees e ON e.id = ta.employee_id
            LEFT JOIN task_executions te ON te.assignment_id = ta.id
            WHERE ts.board_id = %s
              AND ts.is_active = true
              AND e.role IN ('employee', 'team_leader')
              AND e.status = 'active'
        """
        args: list[Any] = [board_id]
        if shift_id:
            query += " AND (ts.shift_id = %s OR ts.shift_id IS NULL) AND e.default_shift_id = %s"
            args.extend([shift_id, shift_id])
        if from_date:
            query += " AND ta.assigned_date >= %s"
            args.append(from_date)
        if to_date:
            query += " AND ta.assigned_date <= %s"
            args.append(to_date)

        query += " ORDER BY e.first_name, e.last_name, ta.assigned_date"
        return await self.fetch_all(query, args)

    async def get_board_stats(self, department_id: UUID | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT
                tb.id AS board_id,
                tb.name AS board_name,
                COUNT(ta.id) AS total_assigned,
                COUNT(ta.id) FILTER (WHERE COALESCE(te.status, 'pending') = 'pending') AS total_pending,
                COUNT(ta.id) FILTER (WHERE te.status = 'in_progress') AS total_in_progress,
                COUNT(ta.id) FILTER (WHERE te.status = 'completed') AS total_completed,
                CASE WHEN COUNT(ta.id) > 0
                     THEN ROUND(COUNT(ta.id) FILTER (WHERE te.status = 'completed')::numeric / COUNT(ta.id) * 100, 1)
                     ELSE 0 END AS completion_pct
            FROM task_boards tb
            LEFT JOIN task_schedules ts ON ts.board_id = tb.id AND ts.is_active = true
            LEFT JOIN task_assignments ta ON ta.schedule_id = ts.id
            LEFT JOIN task_executions te ON te.assignment_id = ta.id
            WHERE tb.is_active = true AND (%s::uuid IS NULL OR tb.department_id = %s)
            GROUP BY tb.id, tb.name
            ORDER BY tb.name
        """
        return await self.fetch_all(query, (department_id, department_id))

    async def get_board_eligible_employees(self, shift_id: UUID | None = None, target_date: date | None = None, department_id: UUID | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT e.id, e.employee_code, e.first_name, e.last_name, e.gender, e.phone, e.email,
                   e.hire_date, e.role, e.department_id, e.position, e.default_shift_id,
                   e.weekly_off_days, e.can_cover_night_shift, e.status, e.profile_image,
                   e.last_login, e.created_at, e.updated_at, e.created_by
            FROM employees e
            WHERE e.role = 'employee' AND e.status = 'active'
        """
        args: list[Any] = []
        if shift_id:
            query += " AND e.default_shift_id = %s"
            args.append(shift_id)
        if department_id:
            query += " AND e.department_id = %s"
            args.append(department_id)
        if target_date:
            query += """
                AND NOT EXISTS (
                    SELECT 1 FROM leaves l
                    WHERE l.employee_id = e.id
                      AND l.status IN ('approved_by_manager', 'approved_by_team_leader')
                      AND %s::date BETWEEN l.start_date AND l.end_date
                )
                AND NOT EXISTS (
                    SELECT 1 FROM employee_shifts es
                    WHERE es.employee_id = e.id
                      AND es.shift_date = %s::date
                      AND es.shift_status IN ('off', 'leave', 'vacation')
                )
            """
            args.extend([target_date, target_date])

        query += " ORDER BY e.first_name, e.last_name"
        return await self.fetch_all(query, args)

    # ── Employee Weekly View ──────────────────────────────────────────────────

    async def get_my_weekly_tasks(self, employee_id: UUID, week_start: date, week_end: date) -> list[dict[str, Any]]:
        query = """
            SELECT
                ta.id AS assignment_id, ta.assigned_date,
                ts.title AS task_title, ts.description AS task_description,
                tb.name AS board_name, sh.name AS shift_name, sh.shift_code, sh.color_code AS shift_color,
                te.id AS execution_id, COALESCE(te.status, 'pending') AS status,
                te.completion_type, te.started_at, te.completed_at, te.notes
            FROM task_assignments ta
            JOIN task_schedules ts ON ts.id = ta.schedule_id
            LEFT JOIN task_boards tb ON tb.id = ts.board_id
            LEFT JOIN shifts sh ON sh.id = ts.shift_id
            LEFT JOIN task_executions te ON te.assignment_id = ta.id
            WHERE ta.employee_id = %s AND ta.assigned_date >= %s AND ta.assigned_date <= %s
            ORDER BY ta.assigned_date, ts.title
        """
        return await self.fetch_all(query, (employee_id, week_start, week_end))

    # ── Task Assignments ──────────────────────────────────────────────────────

    async def get_assignments_by_date(self, target_date: date) -> list[dict[str, Any]]:
        query = """
            SELECT ta.id, ta.schedule_id, ta.employee_id, ta.assigned_date, ta.assigned_by, ta.created_at
            FROM task_assignments ta
            JOIN employees e ON e.id = ta.employee_id
            WHERE ta.assigned_date = %s AND e.role IN ('employee', 'team_leader') AND e.status = 'active'
            ORDER BY ta.created_at
        """
        return await self.fetch_all(query, (target_date,))

    async def get_assignments_by_employee(self, employee_id: UUID, target_date: date) -> list[dict[str, Any]]:
        query = """
            SELECT ta.id, ta.schedule_id, ta.employee_id, ta.assigned_date, ta.assigned_by, ta.created_at
            FROM task_assignments ta
            JOIN employees e ON e.id = ta.employee_id
            WHERE ta.employee_id = %s AND ta.assigned_date = %s AND e.role IN ('employee', 'team_leader') AND e.status = 'active'
            ORDER BY ta.created_at
        """
        return await self.fetch_all(query, (employee_id, target_date))

    async def get_tasks_by_assignee(self, employee_id: UUID) -> list[dict[str, Any]]:
        query = """
            SELECT te.id, te.assignment_id, te.status, te.started_at, te.completed_at, te.notes, te.attachments, te.created_at, te.updated_at
            FROM task_executions te
            JOIN task_assignments ta ON ta.id = te.assignment_id
            WHERE ta.employee_id = %s
        """
        return await self.fetch_all(query, (employee_id,))

    async def count_assignments_by_schedule_and_date(self, schedule_id: UUID, target_date: date) -> int:
        count = await self.fetch_scalar(
            "SELECT COUNT(*) FROM task_assignments WHERE schedule_id = %s AND assigned_date = %s",
            (schedule_id, target_date)
        )
        return count or 0

    async def count_assignments_by_schedule_date_and_shift(self, schedule_id: UUID, target_date: date, shift_id: UUID) -> int:
        count = await self.fetch_scalar(
            """SELECT COUNT(*) FROM task_assignments ta
               JOIN employees e ON e.id = ta.employee_id
               WHERE ta.schedule_id = %s AND ta.assigned_date = %s AND e.default_shift_id = %s""",
            (schedule_id, target_date, shift_id)
        )
        return count or 0

    async def create_assignment(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO task_assignments (schedule_id, employee_id, assigned_date, assigned_by)
               VALUES (%(schedule_id)s, %(employee_id)s, %(assigned_date)s, %(assigned_by)s) RETURNING id, created_at""",
            data,
        )

    async def delete_assignment(self, assignment_id: UUID) -> None:
        await self.execute("DELETE FROM task_executions WHERE assignment_id = %s", (assignment_id,))
        await self.execute("DELETE FROM task_assignments WHERE id = %s", (assignment_id,))

    async def swap_assignments_between_employees(self, emp_a: UUID, emp_b: UUID, target_date: date) -> None:
        await self.execute(
            """UPDATE task_assignments
               SET employee_id = CASE
                   WHEN employee_id = %s THEN %s::uuid
                   WHEN employee_id = %s THEN %s::uuid
                   ELSE employee_id
               END
               WHERE assigned_date = %s AND employee_id IN (%s, %s)""",
            (emp_a, emp_b, emp_b, emp_a, target_date, emp_a, emp_b),
        )

    # ── Task Executions ───────────────────────────────────────────────────────

    async def get_execution_by_assignment(self, assignment_id: UUID) -> dict[str, Any] | None:
        return await self.fetch_one(
            """SELECT id, assignment_id, status, started_at, completed_at, notes, attachments, created_at, updated_at
               FROM task_executions WHERE assignment_id = %s""",
            (assignment_id,),
        )

    async def get_assignment_date_by_execution(self, execution_id: UUID) -> date | None:
        return await self.fetch_scalar(
            """SELECT ta.assigned_date FROM task_assignments ta
               JOIN task_executions te ON te.assignment_id = ta.id WHERE te.id = %s""",
            (execution_id,)
        )

    async def create_execution(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            "INSERT INTO task_executions (assignment_id, status) VALUES (%(assignment_id)s, %(status)s) RETURNING id, created_at, updated_at",
            data,
        )

    async def start_execution(self, execution_id: UUID) -> int:
        return await self.execute(
            "UPDATE task_executions SET status = 'in_progress', started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (execution_id,),
        )

    async def update_execution_status(self, execution_id: UUID, status: str, notes: str | None) -> int:
        return await self.execute(
            "UPDATE task_executions SET status = %s, notes = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (status, notes, execution_id),
        )

    async def complete_execution(self, execution_id: UUID, completion_type: str, notes: str | None) -> int:
        return await self.execute(
            """UPDATE task_executions
               SET status = 'completed', completion_type = %s, completed_at = CURRENT_TIMESTAMP, notes = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (completion_type, notes, execution_id),
        )

    async def get_task_history(self, target_date: date, board_id: UUID | None = None, department_id: UUID | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT
                ta.id AS assignment_id, te.id AS execution_id, ta.assigned_date,
                ts.title AS task_title, ts.description AS task_description, tb.name AS board_name,
                e.id AS employee_id, e.first_name || ' ' || e.last_name AS employee_name,
                e.employee_code, e.profile_image,
                te.status, te.completion_type, te.started_at, te.completed_at, te.notes
            FROM task_assignments ta
            JOIN task_schedules ts ON ts.id = ta.schedule_id
            JOIN employees e ON e.id = ta.employee_id
            JOIN task_executions te ON te.assignment_id = ta.id
            LEFT JOIN task_boards tb ON tb.id = ts.board_id
            WHERE ta.assigned_date = %s
        """
        args: list[Any] = [target_date]
        if board_id:
            query += " AND ts.board_id = %s"
            args.append(board_id)
        if department_id:
            query += " AND tb.department_id = %s"
            args.append(department_id)

        query += " ORDER BY te.completed_at DESC NULLS LAST, e.first_name"
        return await self.fetch_all(query, args)

    # ── Recurring Assignments ─────────────────────────────────────────────────

    async def create_recurring_assignment(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return await self.execute_returning(
            """INSERT INTO task_recurring_assignments (schedule_id, employee_id, day_of_week, assigned_by)
               VALUES (%(schedule_id)s, %(employee_id)s, %(day_of_week)s, %(assigned_by)s)
               ON CONFLICT (schedule_id, employee_id, day_of_week) DO NOTHING
               RETURNING id, created_at""",
            data,
        )

    async def get_recurring_assignments_by_board(self, board_id: UUID) -> list[dict[str, Any]]:
        query = """
            SELECT ra.id, ra.schedule_id, ra.employee_id, ra.day_of_week, ra.assigned_by, ra.created_at
            FROM task_recurring_assignments ra
            JOIN task_schedules ts ON ts.id = ra.schedule_id
            WHERE ts.board_id = %s AND ts.is_active = true
            ORDER BY ra.day_of_week, ra.employee_id
        """
        return await self.fetch_all(query, (board_id,))

    async def delete_recurring_assignment(self, recurring_id: UUID) -> None:
        row = await self.fetch_one(
            "SELECT schedule_id, employee_id, day_of_week FROM task_recurring_assignments WHERE id = %s",
            (recurring_id,)
        )
        if not row:
            return

        await self.execute("DELETE FROM task_recurring_assignments WHERE id = %s", (recurring_id,))

        # Cascading clean up of future non-completed task assignments
        await self.execute(
            """DELETE FROM task_assignments
               WHERE schedule_id = %s AND employee_id = %s AND EXTRACT(DOW FROM assigned_date) = %s
                 AND assigned_date >= CURRENT_DATE
                 AND NOT EXISTS (
                     SELECT 1 FROM task_executions te
                     WHERE te.assignment_id = task_assignments.id AND te.status IN ('in_progress', 'completed')
                 )""",
            (row["schedule_id"], row["employee_id"], row["day_of_week"]),
        )

    async def delete_recurring_assignment_by_key(self, schedule_id: UUID, employee_id: UUID, day_of_week: int) -> None:
        await self.execute(
            "DELETE FROM task_recurring_assignments WHERE schedule_id = %s AND employee_id = %s AND day_of_week = %s",
            (schedule_id, employee_id, day_of_week),
        )
        await self.execute(
            """DELETE FROM task_assignments
               WHERE schedule_id = %s AND employee_id = %s AND EXTRACT(DOW FROM assigned_date) = %s
                 AND assigned_date >= CURRENT_DATE
                 AND NOT EXISTS (
                     SELECT 1 FROM task_executions te
                     WHERE te.assignment_id = task_assignments.id AND te.status IN ('in_progress', 'completed')
                 )""",
            (schedule_id, employee_id, day_of_week),
        )

    async def materialize_recurring_for_date_range(self, board_id: UUID, from_date: date, to_date: date) -> None:
        query = """
            WITH date_series AS (
                SELECT d::date AS assigned_date, EXTRACT(DOW FROM d)::int AS dow
                FROM generate_series(%s::date, %s::date, '1 day'::interval) AS d
            ),
            new_assignments AS (
                INSERT INTO task_assignments (schedule_id, employee_id, assigned_date, assigned_by)
                SELECT ra.schedule_id, ra.employee_id, ds.assigned_date, ra.assigned_by
                FROM task_recurring_assignments ra
                JOIN task_schedules ts ON ts.id = ra.schedule_id
                CROSS JOIN date_series ds
                WHERE ts.board_id = %s AND ts.is_active = true AND ds.dow = ra.day_of_week
                ON CONFLICT (schedule_id, employee_id, assigned_date) DO NOTHING
                RETURNING id
            ),
            ensure_new AS (
                INSERT INTO task_executions (assignment_id, status)
                SELECT id, 'pending' FROM new_assignments
                ON CONFLICT (assignment_id) DO NOTHING
                RETURNING assignment_id
            )
            INSERT INTO task_executions (assignment_id, status)
            SELECT ta.id, 'pending' FROM task_assignments ta
            JOIN task_schedules ts ON ts.id = ta.schedule_id
            WHERE ts.board_id = %s AND ta.assigned_date >= %s AND ta.assigned_date <= %s
              AND NOT EXISTS (SELECT 1 FROM task_executions te WHERE te.assignment_id = ta.id)
            ON CONFLICT (assignment_id) DO NOTHING
        """
        await self.execute(query, (from_date, to_date, board_id, board_id, from_date, to_date))

    async def materialize_all_recurring_for_employee(self, employee_id: UUID, from_date: date, to_date: date) -> None:
        query = """
            WITH date_series AS (
                SELECT d::date AS assigned_date, EXTRACT(DOW FROM d)::int AS dow
                FROM generate_series(%s::date, %s::date, '1 day'::interval) AS d
            ),
            new_assignments AS (
                INSERT INTO task_assignments (schedule_id, employee_id, assigned_date, assigned_by)
                SELECT ra.schedule_id, ra.employee_id, ds.assigned_date, ra.assigned_by
                FROM task_recurring_assignments ra
                JOIN task_schedules ts ON ts.id = ra.schedule_id
                CROSS JOIN date_series ds
                WHERE ra.employee_id = %s AND ts.is_active = true AND ds.dow = ra.day_of_week
                ON CONFLICT (schedule_id, employee_id, assigned_date) DO NOTHING
                RETURNING id
            ),
            ensure_new AS (
                INSERT INTO task_executions (assignment_id, status)
                SELECT id, 'pending' FROM new_assignments
                ON CONFLICT (assignment_id) DO NOTHING
                RETURNING assignment_id
            )
            INSERT INTO task_executions (assignment_id, status)
            SELECT ta.id, 'pending' FROM task_assignments ta
            WHERE ta.employee_id = %s AND ta.assigned_date >= %s AND ta.assigned_date <= %s
              AND NOT EXISTS (SELECT 1 FROM task_executions te WHERE te.assignment_id = ta.id)
            ON CONFLICT (assignment_id) DO NOTHING
        """
        await self.execute(query, (from_date, to_date, employee_id, employee_id, from_date, to_date))

    async def get_execution_assigned_employee(self, execution_id: UUID) -> dict | None:
        """
        Return the employee_id and assignment_id for a given execution.
        Used for authorisation checks (only the assigned employee may act).
        """
        return await self.fetch_one(
            """SELECT ta.employee_id, ta.id AS assignment_id
               FROM task_assignments ta
               JOIN task_executions te ON te.assignment_id = ta.id
               WHERE te.id = %s""",
            (execution_id,),
        )
