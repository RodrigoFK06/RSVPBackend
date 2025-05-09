from pydantic import BaseModel
from typing import List, Optional

class RsvpInput(BaseModel):
    topic: str
    user_id: Optional[str] = None  # 👈 nuevo

class RsvpOutput(BaseModel):
    id: str
    text: str
    words: List[str]
