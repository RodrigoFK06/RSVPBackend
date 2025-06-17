import os

# Ensure required env vars exist before importing the app
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017/testdb")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

import pytest
import pytest_asyncio  # For async fixtures
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from typing import AsyncGenerator
import uuid  # For generating unique emails

from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie
from app.models.rsvp_session import RsvpSession
from app.models.user import User
from app.models.quiz_attempt import QuizAttempt

# Import your FastAPI app instance
from app.main import app
import app.main as main_module

# Patch the database connection to use an in-memory MongoDB
async def fake_connect_to_mongo():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["testdb"],
        document_models=[RsvpSession, User, QuizAttempt],
    )
    return client

main_module.connect_to_mongo = fake_connect_to_mongo
# We won't use placeholder DB functions for now to keep it simpler.
# Tests will run against the database configured by MONGO_URL.
# For true isolation, a more complex setup would be needed.

@pytest_asyncio.fixture(scope="session")
async def test_app_instance():
    async with LifespanManager(app) as manager:
        yield manager.app

@pytest_asyncio.fixture(scope="function")
async def client(test_app_instance) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
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
