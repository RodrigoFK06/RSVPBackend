from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import List, Optional

class RsvpSession(Document):
    topic: str
    text: str
    words: List[str]
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "rsvp_sessions"
