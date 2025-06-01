from pydantic import BaseModel, Field, model_validator
from typing import Optional

class AssistantQueryInput(BaseModel):
    query: str = Field(..., min_length=1, description="User's question or request to the assistant.")
    rsvp_session_id: str

    @model_validator(mode='before')
    @classmethod
    def check_context_source(cls, values):
        if not values.get('rsvp_session_id'):
            raise ValueError('rsvp_session_id must be provided for context.')
        # Optional: check if rsvp_session_id is a valid format if necessary
        return values

class AssistantResponseOutput(BaseModel):
    response: str = Field(..., description="AI-generated response to the user's query.")
