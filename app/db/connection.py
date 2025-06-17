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
    db_name = mongo_url.rsplit("/", 1)[-1]
    await init_beanie(database=client[db_name], document_models=[RsvpSession, User, QuizAttempt])
    return client
