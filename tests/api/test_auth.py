import pytest
from httpx import AsyncClient
from tests.conftest import TEST_PASSWORD

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, admin_token):
    # Admin is created by admin_token fixture if it doesn't exist
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.com",
            "password": TEST_PASSWORD
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_failure(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@test.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_get_me_success(async_client: AsyncClient, admin_token: str):
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401
