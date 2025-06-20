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
    rsvp_session_id: str

    @model_validator(mode='before')
    @classmethod
    def check_input_source(cls, values):
        if not values.get('rsvp_session_id'):
            raise ValueError('rsvp_session_id must be provided.')
        # Optional: check if rsvp_session_id is a valid format if necessary
        return values

class QuizOutput(BaseModel):
    rsvp_session_id: str
    questions: List[QuizQuestion]

class QuizAnswerInput(BaseModel):
    question_id: str
    user_answer: str

class QuizValidateInput(BaseModel):
    rsvp_session_id: str
    answers: List[QuizAnswerInput]
    reading_time_seconds: Optional[int] = None

class QuizQuestionFeedback(BaseModel):
    question_id: str
    is_correct: bool
    feedback: Optional[str] = None
    correct_answer: Optional[str] = None # To show the user the correct answer

class QuizValidateOutput(BaseModel):
    rsvp_session_id: str
    overall_score: float # e.g., percentage
    results: List[QuizQuestionFeedback]
