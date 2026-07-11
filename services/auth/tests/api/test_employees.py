import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_get_employees_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/employees/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_employees(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_create_employee_forbidden(async_client: AsyncClient, user_token: str):
    # Regular employees cannot create users
    response = await async_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "employee_code": "EMP-001",
            "first_name": "New",
            "last_name": "Emp",
            "gender": "male",
            "email": "newemp@test.com",
            "password": "password123",
            "role": "employee",
            "hire_date": "2023-01-01",
            "department_id": str(uuid.uuid4())
        }
    )
    assert response.status_code == 403
    assert "Employees cannot create users" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_employee_admin(async_client: AsyncClient, admin_token: str):
    # Get a department ID first or just use a dummy if foreign keys allow, 
    # but since it's a real DB, it might violate FK if department_id is random.
    # We can either create a department here or omit department_id if it's optional.
    # Let's create a department first to use its ID.
    dept_res = await async_client.post(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Emp Department", "department_code": "DPT-003"}
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    response = await async_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "employee_code": "EMP-002",
            "first_name": "New",
            "last_name": "Emp",
            "gender": "female",
            "email": "newemp2@test.com",
            "password": "password123",
            "role": "employee",
            "hire_date": "2023-01-01",
            "department_id": dept_id,
            "status": "active"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "New"
    assert data["last_name"] == "Emp"
    assert data["email"] == "newemp2@test.com"
    assert "password" not in data  # ensure password is not returned
    
    pytest.created_emp_id = data["id"]

@pytest.mark.asyncio
async def test_get_employee_by_id(async_client: AsyncClient, admin_token: str):
    emp_id = getattr(pytest, "created_emp_id", None)
    if not emp_id:
        pytest.skip("Employee ID not saved")
        
    response = await async_client.get(
        f"/api/v1/employees/{emp_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == emp_id

@pytest.mark.asyncio
async def test_update_employee(async_client: AsyncClient, admin_token: str):
    emp_id = getattr(pytest, "created_emp_id", None)
    if not emp_id:
        pytest.skip("Employee ID not saved")
        
    response = await async_client.put(
        f"/api/v1/employees/{emp_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"first_name": "Updated", "last_name": "Name"}
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"

@pytest.mark.asyncio
async def test_delete_employee(async_client: AsyncClient, admin_token: str):
    emp_id = getattr(pytest, "created_emp_id", None)
    if not emp_id:
        pytest.skip("Employee ID not saved")
        
    response = await async_client.delete(
        f"/api/v1/employees/{emp_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204
    
    # Verify deletion
    response = await async_client.get(
        f"/api/v1/employees/{emp_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
