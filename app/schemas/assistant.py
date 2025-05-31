from pydantic import BaseModel, Field, model_validator
from typing import Optional

class AssistantQueryInput(BaseModel):
    query: str = Field(..., min_length=1, description="User's question or request to the assistant.")
    session_id: Optional[str] = Field(None, description="ID of the active ReadingSession for context.")
    text_context: Optional[str] = Field(None, description="Direct text to be used as context if session_id is not provided.")

    @model_validator(mode='before')
    @classmethod
    def check_context_provided(cls, values):
        if not values.get('session_id') and not values.get('text_context'):
            raise ValueError('Either session_id or text_context must be provided for the assistant.')
        if values.get('session_id') and values.get('text_context'):
            raise ValueError('Provide either session_id or text_context for the assistant, not both.')
        if values.get('text_context') and not values.get('text_context').strip():
            raise ValueError('text_context cannot be empty or just whitespace.')
        return values

class AssistantResponseOutput(BaseModel):
    response: str = Field(..., description="AI-generated response to the user's query.")
