import pytest
from httpx import AsyncClient
import uuid
from datetime import date

@pytest.mark.asyncio
async def test_create_and_get_templates(async_client: AsyncClient, admin_token: str):
    # Setup: Create Dept, Employee, and Shift
    dept_res = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Schedule Dept", "department_code": "DPT-005"}
    )
    dept_id = dept_res.json()["id"]

    emp_res = await async_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "employee_code": "EMP-SCH-1",
            "first_name": "Schedule",
            "last_name": "Emp",
            "gender": "male",
            "email": "schedule@test.com",
            "password": "password123",
            "role": "employee",
            "hire_date": "2023-01-01",
            "department_id": dept_id
        }
    )
    emp_id = emp_res.json()["id"]

    shift_res = await async_client.post(
        "/api/v1/shifts/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Sched Shift",
            "shift_code": "SHT-002",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "department_id": dept_id,
            "color_code": "#000000"
        }
    )
    shift_id = shift_res.json()["id"]

    # 1. Test Create Template
    template_res = await async_client.post(
        "/api/v1/schedules/templates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "employee_id": emp_id,
            "shift_id": shift_id,
            "day_of_week": 1, # Monday
            "is_active": True
        }
    )
    assert template_res.status_code == 201
    template_id = template_res.json()["id"]

    # 2. Test Get Templates by Employee
    get_res = await async_client.get(
        f"/api/v1/schedules/templates/employee/{emp_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1
    
    # 3. Test Delete Template
    del_res = await async_client.delete(
        f"/api/v1/schedules/templates/{template_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 204

@pytest.mark.asyncio
async def test_employee_shifts(async_client: AsyncClient, admin_token: str):
    # Rely on existing test data if possible, or create minimum required
    # Create Dept, Employee, Shift
    dept_res = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Emp Shift Dept", "department_code": "DPT-006"}
    )
    dept_id = dept_res.json()["id"]

    emp_res = await async_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "employee_code": "EMP-SCH-2",
            "first_name": "Shift",
            "last_name": "Emp",
            "gender": "male",
            "email": "shiftemp@test.com",
            "password": "password123",
            "role": "employee",
            "hire_date": "2023-01-01",
            "department_id": dept_id
        }
    )
    emp_id = emp_res.json()["id"]

    shift_res = await async_client.post(
        "/api/v1/shifts/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Day Shift",
            "shift_code": "SHT-003",
            "start_time": "10:00:00",
            "end_time": "18:00:00",
            "department_id": dept_id,
            "color_code": "#111111"
        }
    )
    shift_id = shift_res.json()["id"]

    from datetime import timedelta
    today_date = date.today()
    week_start = today_date - timedelta(days=today_date.weekday())
    week_end = week_start + timedelta(days=6)

    ws_res = await async_client.post(
        "/api/v1/schedules/weekly",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "week_start_date": str(week_start),
            "week_end_date": str(week_end)
        }
    )
    assert ws_res.status_code == 201, ws_res.text
    ws_id = ws_res.json()["id"]

    # 1. Create Employee Shift
    today = str(date.today())
    create_res = await async_client.post(
        "/api/v1/schedules/shifts",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "schedule_id": ws_id,
            "employee_id": emp_id,
            "shift_id": shift_id,
            "shift_date": today,
            "shift_status": "working"
        }
    )
    assert create_res.status_code == 201, create_res.text
    emp_shift_id = create_res.json()["id"]

    # 2. Get Shifts By Date
    get_res = await async_client.get(
        f"/api/v1/schedules/shifts?shift_date={today}&department_id={dept_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1

    # 3. Check-In
    check_in_res = await async_client.post(
        f"/api/v1/schedules/shifts/{emp_shift_id}/check-in",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert check_in_res.status_code == 200

    # 4. Check-Out
    check_out_res = await async_client.post(
        f"/api/v1/schedules/shifts/{emp_shift_id}/check-out",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert check_out_res.status_code == 200
