"""
Full Seed Script for ShiftMaster
Inserts: departments, shifts, employees (admin, managers, team leaders, employees),
         weekly schedule, employee shifts, and task schedules.
Run with:  .venv/Scripts/python scripts/seed_data.py
"""

import sys
import json
from datetime import date, time

import psycopg
from app.core.config import settings
from app.core.security import get_password_hash

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ───────────────────────────────────────────────
# Fixed UUIDs so we can cross-reference them
# ───────────────────────────────────────────────
DEPT_OPS_ID   = "a1000000-0000-0000-0000-000000000001"
DEPT_IT_ID    = "a1000000-0000-0000-0000-000000000002"
DEPT_HR_ID    = "a1000000-0000-0000-0000-000000000003"

SHIFT_MORNING_ID  = "b1000000-0000-0000-0000-000000000001"
SHIFT_EVENING_ID  = "b1000000-0000-0000-0000-000000000002"
SHIFT_NIGHT_ID    = "b1000000-0000-0000-0000-000000000003"

EMP_ADMIN_ID  = "c1000000-0000-0000-0000-000000000001"
EMP_MGR1_ID   = "c1000000-0000-0000-0000-000000000002"
EMP_MGR2_ID   = "c1000000-0000-0000-0000-000000000003"
EMP_TL1_ID    = "c1000000-0000-0000-0000-000000000004"
EMP_TL2_ID    = "c1000000-0000-0000-0000-000000000005"
EMP_EMP1_ID   = "c1000000-0000-0000-0000-000000000006"
EMP_EMP2_ID   = "c1000000-0000-0000-0000-000000000007"
EMP_EMP3_ID   = "c1000000-0000-0000-0000-000000000008"

WEEK_ID = "e1000000-0000-0000-0000-000000000001"
TASK_SCHED1_ID = "d1000000-0000-0000-0000-000000000001"
TASK_SCHED2_ID = "d1000000-0000-0000-0000-000000000002"
TASK_SCHED3_ID = "d1000000-0000-0000-0000-000000000003"


def main():
    with psycopg.connect(settings.db.url, autocommit=True) as conn:

        # ──────────────────────────────────────────
        # 1. DEPARTMENTS
        # ──────────────────────────────────────────
        print("[1/6] Seeding Departments...")
        departments = [
            {
                "id": DEPT_OPS_ID,
                "department_code": "OPS",
                "name": "Operations",
                "description": "Handles day-to-day field operations and logistics.",
                "max_leaves_per_day": 2,
                "active_modules": json.dumps(["shifts", "tasks", "leaves"]),
                "fiberx_enabled": True,
            },
            {
                "id": DEPT_IT_ID,
                "department_code": "IT",
                "name": "Information Technology",
                "description": "Manages systems, infrastructure, and software.",
                "max_leaves_per_day": 2,
                "active_modules": json.dumps(["shifts", "tasks"]),
                "fiberx_enabled": False,
            },
            {
                "id": DEPT_HR_ID,
                "department_code": "HR",
                "name": "Human Resources",
                "description": "Manages hiring, training, and employee welfare.",
                "max_leaves_per_day": 1,
                "active_modules": json.dumps(["shifts", "leaves"]),
                "fiberx_enabled": False,
            },
        ]
        for d in departments:
            conn.execute("""
                INSERT INTO departments (id, department_code, name, description, max_leaves_per_day, active_modules, fiberx_enabled)
                VALUES (%(id)s, %(department_code)s, %(name)s, %(description)s, %(max_leaves_per_day)s, %(active_modules)s, %(fiberx_enabled)s)
                ON CONFLICT (id) DO NOTHING
            """, d)
        print(f"   ✓ {len(departments)} departments inserted.")

        # ──────────────────────────────────────────
        # 2. SHIFTS
        # ──────────────────────────────────────────
        print("[2/6] Seeding Shifts...")
        shifts = [
            {
                "id": SHIFT_MORNING_ID,
                "shift_code": "MORN",
                "name": "Morning Shift",
                "name_en": "Morning",
                "start_time": time(7, 0),
                "end_time": time(15, 0),
                "color_code": "#3B82F6",
                "requires_vehicle": False,
                "min_rest_hours": 8,
                "department_id": None,
            },
            {
                "id": SHIFT_EVENING_ID,
                "shift_code": "EVE",
                "name": "Evening Shift",
                "name_en": "Evening",
                "start_time": time(15, 0),
                "end_time": time(23, 0),
                "color_code": "#F59E0B",
                "requires_vehicle": False,
                "min_rest_hours": 8,
                "department_id": None,
            },
            {
                "id": SHIFT_NIGHT_ID,
                "shift_code": "NGT",
                "name": "Night Shift",
                "name_en": "Night",
                "start_time": time(23, 0),
                "end_time": time(7, 0),
                "color_code": "#6366F1",
                "requires_vehicle": False,
                "min_rest_hours": 10,
                "department_id": None,
            },
        ]
        for s in shifts:
            conn.execute("""
                INSERT INTO shifts (id, shift_code, name, name_en, start_time, end_time, color_code, requires_vehicle, min_rest_hours, department_id)
                VALUES (%(id)s, %(shift_code)s, %(name)s, %(name_en)s, %(start_time)s, %(end_time)s, %(color_code)s, %(requires_vehicle)s, %(min_rest_hours)s, %(department_id)s)
                ON CONFLICT (id) DO NOTHING
            """, s)
        print(f"   ✓ {len(shifts)} shifts inserted.")

        # ──────────────────────────────────────────
        # 3. EMPLOYEES  (admin, managers, team leaders, employees)
        # ──────────────────────────────────────────
        print("[3/6] Seeding Employees...")
        employees = [
            # Admin
            {
                "id": EMP_ADMIN_ID, "employee_code": "ADM001",
                "first_name": "System", "last_name": "Admin",
                "gender": "male", "phone": "07700000001",
                "email": "admin@swibit.com",
                "password_hash": get_password_hash("admin123"),
                "hire_date": date(2024, 1, 1), "role": "admin",
                "department_id": None, "default_shift_id": SHIFT_MORNING_ID,
                "weekly_off_days": 2, "can_cover_night_shift": False,
                "can_create_tables": True, "can_manage_help_docs": True,
                "can_post_announcements": True, "can_manage_fiberx_data": True,
                "status": "active",
            },
            # Manager 1 – Operations
            {
                "id": EMP_MGR1_ID, "employee_code": "MGR001",
                "first_name": "Ali", "last_name": "Hassan",
                "gender": "male", "phone": "07700000002",
                "email": "ali.manager@swibit.com",
                "password_hash": get_password_hash("manager123"),
                "hire_date": date(2024, 2, 1), "role": "manager",
                "department_id": DEPT_OPS_ID, "default_shift_id": SHIFT_MORNING_ID,
                "weekly_off_days": 2, "can_cover_night_shift": False,
                "can_create_tables": False, "can_manage_help_docs": False,
                "can_post_announcements": True, "can_manage_fiberx_data": False,
                "status": "active",
            },
            # Manager 2 – IT
            {
                "id": EMP_MGR2_ID, "employee_code": "MGR002",
                "first_name": "Sara", "last_name": "Ahmed",
                "gender": "female", "phone": "07700000003",
                "email": "sara.manager@swibit.com",
                "password_hash": get_password_hash("manager123"),
                "hire_date": date(2024, 2, 15), "role": "manager",
                "department_id": DEPT_IT_ID, "default_shift_id": SHIFT_MORNING_ID,
                "weekly_off_days": 2, "can_cover_night_shift": False,
                "can_create_tables": False, "can_manage_help_docs": False,
                "can_post_announcements": True, "can_manage_fiberx_data": False,
                "status": "active",
            },
            # Team Leader 1 – Operations (Morning)
            {
                "id": EMP_TL1_ID, "employee_code": "TL001",
                "first_name": "Omar", "last_name": "Karimi",
                "gender": "male", "phone": "07700000004",
                "email": "omar.tl@swibit.com",
                "password_hash": get_password_hash("leader123"),
                "hire_date": date(2024, 3, 1), "role": "team_leader",
                "department_id": DEPT_OPS_ID, "default_shift_id": SHIFT_MORNING_ID,
                "weekly_off_days": 2, "can_cover_night_shift": True,
                "can_create_tables": False, "can_manage_help_docs": False,
                "can_post_announcements": False, "can_manage_fiberx_data": False,
                "status": "active",
            },
            # Team Leader 2 – IT (Evening)
            {
                "id": EMP_TL2_ID, "employee_code": "TL002",
                "first_name": "Nour", "last_name": "Khalil",
                "gender": "female", "phone": "07700000005",
                "email": "nour.tl@swibit.com",
                "password_hash": get_password_hash("leader123"),
                "hire_date": date(2024, 3, 15), "role": "team_leader",
                "department_id": DEPT_IT_ID, "default_shift_id": SHIFT_EVENING_ID,
                "weekly_off_days": 2, "can_cover_night_shift": False,
                "can_create_tables": False, "can_manage_help_docs": False,
                "can_post_announcements": False, "can_manage_fiberx_data": False,
                "status": "active",
            },
            # Employee 1 – Morning, Operations
            {
                "id": EMP_EMP1_ID, "employee_code": "EMP001",
                "first_name": "Haider", "last_name": "Bassem",
                "gender": "male", "phone": "07700000006",
                "email": "haider@swibit.com",
                "password_hash": get_password_hash("emp123"),
                "hire_date": date(2024, 4, 1), "role": "employee",
                "department_id": DEPT_OPS_ID, "default_shift_id": SHIFT_MORNING_ID,
                "weekly_off_days": 2, "can_cover_night_shift": False,
                "can_create_tables": False, "can_manage_help_docs": False,
                "can_post_announcements": False, "can_manage_fiberx_data": False,
                "status": "active",
            },
            # Employee 2 – Evening, IT
            {
                "id": EMP_EMP2_ID, "employee_code": "EMP002",
                "first_name": "Lana", "last_name": "Saeed",
                "gender": "female", "phone": "07700000007",
                "email": "lana@swibit.com",
                "password_hash": get_password_hash("emp123"),
                "hire_date": date(2024, 4, 10), "role": "employee",
                "department_id": DEPT_IT_ID, "default_shift_id": SHIFT_EVENING_ID,
                "weekly_off_days": 2, "can_cover_night_shift": False,
                "can_create_tables": False, "can_manage_help_docs": False,
                "can_post_announcements": False, "can_manage_fiberx_data": False,
                "status": "active",
            },
            # Employee 3 – Night, Operations
            {
                "id": EMP_EMP3_ID, "employee_code": "EMP003",
                "first_name": "Zaid", "last_name": "Nouri",
                "gender": "male", "phone": "07700000008",
                "email": "zaid@swibit.com",
                "password_hash": get_password_hash("emp123"),
                "hire_date": date(2024, 4, 20), "role": "employee",
                "department_id": DEPT_OPS_ID, "default_shift_id": SHIFT_NIGHT_ID,
                "weekly_off_days": 2, "can_cover_night_shift": True,
                "can_create_tables": False, "can_manage_help_docs": False,
                "can_post_announcements": False, "can_manage_fiberx_data": False,
                "status": "active",
            },
        ]
        for e in employees:
            conn.execute("""
                INSERT INTO employees (
                    id, employee_code, first_name, last_name, gender, phone, email,
                    password_hash, hire_date, role, department_id, default_shift_id,
                    weekly_off_days, can_cover_night_shift, can_create_tables,
                    can_manage_help_docs, can_post_announcements, can_manage_fiberx_data,
                    status
                ) VALUES (
                    %(id)s, %(employee_code)s, %(first_name)s, %(last_name)s, %(gender)s,
                    %(phone)s, %(email)s, %(password_hash)s, %(hire_date)s, %(role)s,
                    %(department_id)s, %(default_shift_id)s, %(weekly_off_days)s,
                    %(can_cover_night_shift)s, %(can_create_tables)s,
                    %(can_manage_help_docs)s, %(can_post_announcements)s,
                    %(can_manage_fiberx_data)s, %(status)s
                )
                ON CONFLICT (email) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name  = EXCLUDED.last_name,
                    role       = EXCLUDED.role,
                    status     = EXCLUDED.status
            """, e)
        print(f"   ✓ {len(employees)} employees inserted.")

        # ──────────────────────────────────────────
        # 4. DEPARTMENT MANAGERS (link table)
        # ──────────────────────────────────────────
        print("[4/6] Seeding Department Manager Links...")
        dept_managers = [
            {"department_id": DEPT_OPS_ID, "manager_id": EMP_MGR1_ID},
            {"department_id": DEPT_IT_ID,  "manager_id": EMP_MGR2_ID},
        ]
        for dm in dept_managers:
            conn.execute("""
                INSERT INTO department_managers (department_id, manager_id)
                VALUES (%(department_id)s, %(manager_id)s)
                ON CONFLICT DO NOTHING
            """, dm)
        print(f"   ✓ {len(dept_managers)} department-manager links inserted.")

        # ──────────────────────────────────────────
        # 5. WEEKLY SCHEDULE + EMPLOYEE SHIFTS
        # ──────────────────────────────────────────
        print("[5/6] Seeding Weekly Schedule (Week: Jun 30 - Jul 6, 2026)...")
        # Resolve actual admin ID (may differ from fixed UUID if row was pre-existing)
        row = conn.execute("SELECT id FROM employees WHERE email = 'admin@swibit.com'").fetchone()
        real_admin_id = str(row[0]) if row else EMP_ADMIN_ID

        conn.execute("""
            INSERT INTO weekly_schedule (id, week_start_date, week_end_date, status, created_by)
            VALUES (%s, %s, %s, 'published', %s)
            ON CONFLICT (id) DO NOTHING
        """, (WEEK_ID, date(2026, 6, 30), date(2026, 7, 6), real_admin_id))

        # 5 weekdays × 3 employees
        employee_shifts_data = [
            (EMP_EMP1_ID, SHIFT_MORNING_ID, date(2026, 6, 30)),
            (EMP_EMP1_ID, SHIFT_MORNING_ID, date(2026, 7, 1)),
            (EMP_EMP1_ID, SHIFT_MORNING_ID, date(2026, 7, 2)),
            (EMP_EMP1_ID, SHIFT_MORNING_ID, date(2026, 7, 3)),
            (EMP_EMP1_ID, SHIFT_MORNING_ID, date(2026, 7, 4)),
            (EMP_EMP2_ID, SHIFT_EVENING_ID, date(2026, 6, 30)),
            (EMP_EMP2_ID, SHIFT_EVENING_ID, date(2026, 7, 1)),
            (EMP_EMP2_ID, SHIFT_EVENING_ID, date(2026, 7, 2)),
            (EMP_EMP2_ID, SHIFT_EVENING_ID, date(2026, 7, 3)),
            (EMP_EMP2_ID, SHIFT_EVENING_ID, date(2026, 7, 4)),
            (EMP_EMP3_ID, SHIFT_NIGHT_ID,   date(2026, 6, 30)),
            (EMP_EMP3_ID, SHIFT_NIGHT_ID,   date(2026, 7, 1)),
            (EMP_EMP3_ID, SHIFT_NIGHT_ID,   date(2026, 7, 2)),
            (EMP_EMP3_ID, SHIFT_NIGHT_ID,   date(2026, 7, 3)),
            (EMP_EMP3_ID, SHIFT_NIGHT_ID,   date(2026, 7, 4)),
        ]
        for emp_id, shift_id, shift_date in employee_shifts_data:
            conn.execute("""
                INSERT INTO employee_shifts (schedule_id, employee_id, shift_id, shift_date, shift_status, created_by)
                VALUES (%s, %s, %s, %s, 'working', %s)
                ON CONFLICT DO NOTHING
            """, (WEEK_ID, emp_id, shift_id, shift_date, real_admin_id))
        print(f"   ✓ 1 weekly schedule + {len(employee_shifts_data)} employee shifts inserted.")

        # ──────────────────────────────────────────
        # 6. TASK SCHEDULES
        # ──────────────────────────────────────────
        print("[6/6] Seeding Task Schedules...")
        task_schedules = [
            {
                "id": TASK_SCHED1_ID,
                "title": "Morning Cleaning",
                "description": "Clean common areas at the start of morning shift.",
                "schedule_type": "recurring",
                "shift_id": SHIFT_MORNING_ID,
                "recurrence": "daily",
                "recurrence_days": [1, 2, 3, 4, 5],
                "max_assignees": 2,
                "is_active": True,
                "created_by": EMP_MGR1_ID,
            },
            {
                "id": TASK_SCHED2_ID,
                "title": "Evening Security Check",
                "description": "Inspect all exits and lock all rooms at end of evening shift.",
                "schedule_type": "recurring",
                "shift_id": SHIFT_EVENING_ID,
                "recurrence": "daily",
                "recurrence_days": [1, 2, 3, 4, 5],
                "max_assignees": 1,
                "is_active": True,
                "created_by": EMP_MGR1_ID,
            },
            {
                "id": TASK_SCHED3_ID,
                "title": "Weekly IT System Backup",
                "description": "Run full system backup every Monday night.",
                "schedule_type": "recurring",
                "shift_id": SHIFT_NIGHT_ID,
                "recurrence": "periodic",
                "recurrence_days": [1],
                "max_assignees": 1,
                "is_active": True,
                "created_by": EMP_MGR2_ID,
            },
        ]
        for t in task_schedules:
            conn.execute("""
                INSERT INTO task_schedules (id, title, description, schedule_type, shift_id, recurrence, recurrence_days, max_assignees, is_active, created_by)
                VALUES (%(id)s, %(title)s, %(description)s, %(schedule_type)s, %(shift_id)s, %(recurrence)s, %(recurrence_days)s, %(max_assignees)s, %(is_active)s, %(created_by)s)
                ON CONFLICT (id) DO NOTHING
            """, t)
        print(f"   ✓ {len(task_schedules)} task schedules inserted.")

        print()
        print("=" * 56)
        print("SEED COMPLETE — Login Credentials")
        print("=" * 56)
        print(f"{'Role':<14} {'Email':<30} {'Password'}")
        print(f"{'-'*14} {'-'*30} {'-'*12}")
        print(f"{'Admin':<14} {'admin@swibit.com':<30} admin123")
        print(f"{'Manager':<14} {'ali.manager@swibit.com':<30} manager123")
        print(f"{'Manager':<14} {'sara.manager@swibit.com':<30} manager123")
        print(f"{'Team Leader':<14} {'omar.tl@swibit.com':<30} leader123")
        print(f"{'Team Leader':<14} {'nour.tl@swibit.com':<30} leader123")
        print(f"{'Employee':<14} {'haider@swibit.com':<30} emp123")
        print(f"{'Employee':<14} {'lana@swibit.com':<30} emp123")
        print(f"{'Employee':<14} {'zaid@swibit.com':<30} emp123")


if __name__ == "__main__":
    main()
