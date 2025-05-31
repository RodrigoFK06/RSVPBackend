from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class SessionStatDetail(BaseModel):
    session_id: str
    text_snippet: Optional[str] = None # First N words of the text
    word_count: Optional[int] = None
    reading_time_seconds: Optional[int] = None
    wpm: Optional[float] = None
    quiz_taken: bool = False
    quiz_score: Optional[float] = None # Percentage
    ai_text_difficulty: Optional[str] = None
    ai_estimated_ideal_reading_time_seconds: Optional[int] = None
    created_at: datetime

class UserOverallStats(BaseModel):
    total_sessions_read: int
    total_reading_time_seconds: int
    total_words_read: int
    average_wpm: Optional[float] = None
    total_quizzes_taken: int
    average_quiz_score: Optional[float] = None # Percentage

class PersonalizedFeedback(BaseModel):
    feedback_text: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    # Could add areas_of_strength, areas_for_improvement etc.

class UserStatsOutput(BaseModel):
    user_id: str
    overall_stats: UserOverallStats
    recent_sessions_stats: List[SessionStatDetail] = []
    personalized_feedback: Optional[PersonalizedFeedback] = None # To be added later
