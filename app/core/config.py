import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret_key_if_not_set")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

settings = Settings()
