import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_get_audit_by_table_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/audit/table/employees")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_audit_by_table(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        "/api/v1/audit/table/employees",
        headers={"X-User-Id": admin_token}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_audit_by_employee(async_client: AsyncClient, admin_token: str):
    emp_id = str(uuid.uuid4())
    response = await async_client.get(
        f"/api/v1/audit/employee/{emp_id}",
        headers={"X-User-Id": admin_token}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
