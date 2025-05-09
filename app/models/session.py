from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict


class PromptResult(BaseModel):
    summary: str
    explanation: str
    questions: List[str]
    glossary: Optional[Dict[str, str]] = None


class ReadingSession(Document):
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    results: Optional[PromptResult] = None

    class Settings:
        name = "reading_sessions"
