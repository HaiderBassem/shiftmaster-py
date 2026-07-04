import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_get_departments_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/departments/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_department_user(async_client: AsyncClient, user_token: str):
    # Regular user cannot create department
    response = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "Test Department"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_department_admin(async_client: AsyncClient, admin_token: str):
    response = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Test Department"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Department"
    assert "id" in data
    
    # Store ID for next tests
    pytest.created_dept_id = data["id"]

@pytest.mark.asyncio
async def test_get_departments(async_client: AsyncClient, user_token: str):
    response = await async_client.get(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_get_department_by_id(async_client: AsyncClient, user_token: str):
    dept_id = getattr(pytest, "created_dept_id", None)
    if not dept_id:
        pytest.skip("Department ID not saved")
        
    response = await async_client.get(
        f"/api/v1/departments/{dept_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == dept_id

@pytest.mark.asyncio
async def test_update_department_admin(async_client: AsyncClient, admin_token: str):
    dept_id = getattr(pytest, "created_dept_id", None)
    if not dept_id:
        pytest.skip("Department ID not saved")
        
    response = await async_client.put(
        f"/api/v1/departments/{dept_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Updated Department"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Department"
