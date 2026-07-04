import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_get_schedules_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/tasks/schedules")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_schedule_forbidden(async_client: AsyncClient, user_token: str):
    response = await async_client.post(
        "/api/v1/tasks/schedules",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "task_name": "Test Task",
            "department_id": str(uuid.uuid4()),
            "priority": "high"
        }
    )
    # user_token is a regular employee, cannot create schedule
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_schedule_admin(async_client: AsyncClient, admin_token: str):
    # Setup: Create Dept
    dept_res = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Tasks Dept"}
    )
    dept_id = dept_res.json()["id"]

    response = await async_client.post(
        "/api/v1/tasks/schedules",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "task_name": "Test Schedule Task",
            "department_id": dept_id,
            "priority": "high",
            "recurrence_pattern": "daily",
            "is_active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task_name"] == "Test Schedule Task"
    
    pytest.created_schedule_id = data["id"]

@pytest.mark.asyncio
async def test_get_schedules(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        "/api/v1/tasks/schedules",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_board_view(async_client: AsyncClient, admin_token: str):
    # Just test that the endpoint responds correctly for a random board_id
    # If the board doesn't exist, it might return empty list or 404
    board_id = str(uuid.uuid4())
    response = await async_client.get(
        f"/api/v1/tasks/boards/{board_id}/view",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Either 200 with [] or 404
    assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_execution_start_not_found(async_client: AsyncClient, admin_token: str):
    exec_id = str(uuid.uuid4())
    response = await async_client.post(
        f"/api/v1/tasks/executions/{exec_id}/start",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Depending on how it's implemented, might be 404 or 403 (since assigned_emp_id logic)
    # The code queries DB first, so if not found it returns None, assigned_emp_id != current_user => 403
    assert response.status_code in [403, 404]
