import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_shifts_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/shifts/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_shift(async_client: AsyncClient, admin_token: str):
    # Create department first
    dept_res = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Shift Department", "department_code": "SHT-001"}
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    response = await async_client.post(
        "/api/v1/shifts/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Morning Shift",
            "shift_code": "SHT-001",
            "start_time": "08:00:00",
            "end_time": "16:00:00",
            "department_id": dept_id,
            "color_code": "#FFFFFF"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Morning Shift"
    
    pytest.created_shift_id = data["id"]
    pytest.shift_dept_id = dept_id

@pytest.mark.asyncio
async def test_get_shifts(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        "/api/v1/shifts/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_get_shift_by_id(async_client: AsyncClient, admin_token: str):
    shift_id = getattr(pytest, "created_shift_id", None)
    if not shift_id:
        pytest.skip("Shift ID not saved")
        
    response = await async_client.get(
        f"/api/v1/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == shift_id

@pytest.mark.asyncio
async def test_update_shift(async_client: AsyncClient, admin_token: str):
    shift_id = getattr(pytest, "created_shift_id", None)
    if not shift_id:
        pytest.skip("Shift ID not saved")
        
    response = await async_client.put(
        f"/api/v1/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Updated Morning Shift"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Morning Shift"

@pytest.mark.asyncio
async def test_delete_shift(async_client: AsyncClient, admin_token: str):
    shift_id = getattr(pytest, "created_shift_id", None)
    if not shift_id:
        pytest.skip("Shift ID not saved")
        
    response = await async_client.delete(
        f"/api/v1/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204
    
    # Verify deletion
    response = await async_client.get(
        f"/api/v1/shifts/{shift_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
