import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_manage_handover(async_client: AsyncClient, admin_token: str):
    # Setup: Create Dept, Employee, Shift
    dept_res = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Handover Dept", "department_code": "DPT-004"}
    )
    dept_id = dept_res.json()["id"]

    emp_res = await async_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "employee_code": "EMP-HND-1",
            "first_name": "Handover",
            "last_name": "Emp",
            "gender": "male",
            "email": "handover@test.com",
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
            "name": "Handover Shift",
            "shift_code": "SHT-004",
            "start_time": "12:00:00",
            "end_time": "20:00:00",
            "department_id": dept_id,
            "color_code": "#222222"
        }
    )
    shift_id = shift_res.json()["id"]

    # 1. Create Handover
    create_res = await async_client.post(
        "/api/v1/handovers/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "department_id": dept_id,
            "shift_summary": "Morning shift went well",
            "pending_issues": "Machine 3 is down"
        }
    )
    assert create_res.status_code == 201
    handover_id = create_res.json()["id"]

    # 2. Get Handovers by Department
    get_res = await async_client.get(
        f"/api/v1/handovers/department/{dept_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1

    # 3. Add Comment
    comment_res = await async_client.post(
        f"/api/v1/handovers/{handover_id}/comments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "employee_id": emp_id,
            "comment": "Got it, I will check."
        }
    )
    assert comment_res.status_code == 201

    # 4. Claim Handover
    claim_res = await async_client.post(
        f"/api/v1/handovers/{handover_id}/claim",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert claim_res.status_code == 200

    # 5. Complete Handover
    comp_res = await async_client.post(
        f"/api/v1/handovers/{handover_id}/complete",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert comp_res.status_code == 200
