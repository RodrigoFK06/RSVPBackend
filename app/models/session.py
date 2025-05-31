from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Literal
from app.schemas.quiz import QuizQuestion # We'll store QuizQuestion Pydantic models directly


class PromptResult(BaseModel):
    summary: str
    explanation: str
    questions: List[str]
    glossary: Optional[Dict[str, str]] = None


class ReadingSession(Document):
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None # Indexed if we query by it often
    results: Optional[PromptResult] = None # Summary, explanation etc.
    quiz_questions: Optional[List[QuizQuestion]] = None

    # New fields for statistics
    word_count: Optional[int] = None
    reading_time_seconds: Optional[int] = None # To be set by client or estimated
    ai_estimated_ideal_reading_time_seconds: Optional[int] = None # AI-generated
    ai_text_difficulty: Optional[Literal["easy", "medium", "hard", "unknown"]] = Field(default="unknown") # AI-generated

    class Settings:
        name = "reading_sessions"

    @property
    def calculated_wpm(self) -> Optional[float]:
        if self.word_count and self.reading_time_seconds and self.reading_time_seconds > 0:
            return round((self.word_count / self.reading_time_seconds) * 60, 2)
        return None

    # Method to update word_count, could be called on save or when text is set
    def update_word_count(self):
        if self.text:
            self.word_count = len(self.text.split())
        else:
            self.word_count = 0
