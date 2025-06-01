from pydantic import BaseModel, Field, model_validator
from typing import Optional

class AssistantQueryInput(BaseModel):
    query: str = Field(..., min_length=1, description="User's question or request to the assistant.")
    session_id: Optional[str] = Field(None, description="ID of the active ReadingSession for context.")
    text_context: Optional[str] = Field(None, description="Direct text to be used as context if session_id is not provided.")
    rsvp_session_id: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def check_context_source(cls, values):
        provided_sources = sum([
            1 for v in [values.get('session_id'), values.get('text_context'), values.get('rsvp_session_id')] if v is not None
        ])
        if provided_sources == 0:
            raise ValueError('Either session_id (for ReadingSession), text_context, or rsvp_session_id must be provided for context.')
        if provided_sources > 1:
            raise ValueError('Provide only one of session_id (for ReadingSession), text_context, or rsvp_session_id for context.')
        if values.get('text_context') and not values.get('text_context').strip(): # Keep existing check
            raise ValueError('text_context cannot be empty or just whitespace if provided.')
        return values

class AssistantResponseOutput(BaseModel):
    response: str = Field(..., description="AI-generated response to the user's query.")
