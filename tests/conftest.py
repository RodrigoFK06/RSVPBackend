import pytest
import pytest_asyncio # For async fixtures
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from typing import AsyncGenerator, Callable # For type hinting
import os
import uuid # For generating unique emails

# Import your FastAPI app instance
from app.main import app
# We won't use placeholder DB functions for now to keep it simpler.
# Tests will run against the database configured by MONGO_URL.
# For true isolation, a more complex setup would be needed.

@pytest_asyncio.fixture(scope="session")
async def test_app_instance():
    async with LifespanManager(app) as manager:
        yield manager.app

@pytest_asyncio.fixture(scope="function")
async def client(test_app_instance) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=test_app_instance, base_url="http://127.0.0.1:8000") as ac:
        yield ac

@pytest_asyncio.fixture(scope="function")
async def authenticated_user_token(client: AsyncClient) -> dict:
    unique_email = f"testuser_{uuid.uuid4().hex}@example.com"
    password = "testpassword123"
    user_data = {"email": unique_email, "password": password, "full_name": "Test User"}

    response = await client.post("/auth/register", json=user_data)
    if response.status_code != 201:
        pytest.fail(f"Failed to register user for token: {response.text} (Email: {unique_email})")

    login_data = {"username": unique_email, "password": password}
    response = await client.post("/auth/login", json=login_data)
    if response.status_code != 200:
        pytest.fail(f"Failed to login user for token: {response.text} (Email: {unique_email})")

    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}", "email": unique_email}
