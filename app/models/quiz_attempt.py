from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import List

# Re-using QuizQuestionFeedback from app.schemas.quiz for individual answer results
from app.schemas.quiz import QuizQuestionFeedback

class QuizAttempt(Document):
    reading_session_id: Indexed(str)
    user_id: Indexed(str)
    results: List[QuizQuestionFeedback] # Stores feedback for each question answered
    overall_score: float
    attempted_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "quiz_attempts"
