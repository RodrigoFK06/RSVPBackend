from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import List, Optional, Literal
from app.schemas.quiz import QuizQuestion

class RsvpSession(Document):
    topic: str
    text: str
    words: List[str]
    user_id: Optional[str] = None
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    quiz_questions: Optional[List[QuizQuestion]] = None
    ai_estimated_ideal_reading_time_seconds: Optional[int] = None
    ai_text_difficulty: Optional[Literal["easy", "medium", "hard", "unknown"]] = Field(default="unknown")
    word_count: Optional[int] = None

    def update_word_count(self):
        if self.text:
            self.word_count = len(self.text.split())
        else:
            self.word_count = 0

    class Settings:
        name = "rsvp_sessions"
