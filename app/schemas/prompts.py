from pydantic import BaseModel
from typing import List, Optional, Dict


class PromptInput(BaseModel):
    text: str
    # user_id: Optional[str] = None # REMOVE THIS LINE


class PromptOutput(BaseModel):
    summary: str
    explanation: str
    questions: List[str]
    glossary: Optional[Dict[str, str]] = None
