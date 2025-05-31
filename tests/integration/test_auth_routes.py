import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    unique_email = f"test_{uuid.uuid4().hex}@example.com"
    user_data = {"email": unique_email, "password": "password123", "full_name": "Test User"}
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    response_data = response.json()
    assert response_data["email"] == unique_email
    assert "id" in response_data

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    unique_email = f"login_test_{uuid.uuid4().hex}@example.com"
    password = "securepassword"

    user_data = {"email": unique_email, "password": password, "full_name": "Login Test"}
    reg_response = await client.post("/auth/register", json=user_data)
    assert reg_response.status_code == 201, reg_response.text

    login_data = {"username": unique_email, "password": password}
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200, response.text
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, authenticated_user_token: dict):
    headers = {"Authorization": authenticated_user_token["Authorization"]} # Just the token part
    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 200, response.text
    response_data = response.json()
    assert response_data["email"] == authenticated_user_token["email"]
