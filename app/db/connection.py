import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models.rsvp_session import RsvpSession
from app.models.user import User
from app.models.quiz_attempt import QuizAttempt

load_dotenv()

async def connect_to_mongo() -> AsyncIOMotorClient:
    """Create MongoDB client and initialize Beanie."""
    mongo_url = os.getenv("MONGO_URL")
    if not mongo_url:
        raise ValueError("MONGO_URL environment variable is not set")

    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()  # ✅ forma segura y robusta
    await init_beanie(database=db, document_models=[RsvpSession, User, QuizAttempt])
    return client
