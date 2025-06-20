from pydantic import BaseModel
from typing import List, Optional

class RsvpInput(BaseModel):
    topic: str
    # user_id: Optional[str] = None # REMOVE THIS LINE

class RsvpOutput(BaseModel):
    id: str
    text: str
    words: List[str]
    reading_time_seconds: Optional[int] = None
    wpm: Optional[float] = None
    quiz_score: Optional[float] = None
    quiz_taken: bool = False
