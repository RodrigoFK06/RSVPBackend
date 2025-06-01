from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal

class QuizQuestion(BaseModel):
    id: str = Field(..., description="Unique ID for the question (e.g., generated UUID or hash)")
    question_text: str
    question_type: Literal["multiple_choice", "open_ended"]
    options: Optional[List[str]] = None
    correct_answer: str # For MC, this is the text of the correct option. For open, a model answer.
    explanation: Optional[str] = None # Optional explanation for the correct answer

    class Config:
        orm_mode = True

class QuizCreateInput(BaseModel):
    text: Optional[str] = None
    session_id: Optional[str] = None # To use text from an existing ReadingSession
    rsvp_session_id: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def check_input_source(cls, values):
        provided_sources = sum([
            1 for v in [values.get('text'), values.get('session_id'), values.get('rsvp_session_id')] if v is not None
        ])
        if provided_sources == 0:
            raise ValueError('Either text, session_id (for ReadingSession), or rsvp_session_id must be provided.')
        if provided_sources > 1:
            raise ValueError('Provide only one of text, session_id (for ReadingSession), or rsvp_session_id.')
        if values.get('text') and not values.get('text').strip(): # Keep existing check for empty text
            raise ValueError('text cannot be empty or just whitespace if provided.')
        return values

class QuizOutput(BaseModel):
    reading_session_id: Optional[str] = None # ID of the session if quiz is attached
    questions: List[QuizQuestion]

class QuizAnswerInput(BaseModel):
    question_id: str
    user_answer: str

class QuizValidateInput(BaseModel):
    reading_session_id: str # Identifies the session containing the quiz and questions
    answers: List[QuizAnswerInput]

class QuizQuestionFeedback(BaseModel):
    question_id: str
    is_correct: bool
    feedback: Optional[str] = None
    correct_answer: Optional[str] = None # To show the user the correct answer

class QuizValidateOutput(BaseModel):
    reading_session_id: str
    overall_score: float # e.g., percentage
    results: List[QuizQuestionFeedback]
