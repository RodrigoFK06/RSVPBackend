from beanie import Document, Indexed
from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime

class User(Document):
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) # Will need a pre_save hook to update this

    class Settings:
        name = "users"
