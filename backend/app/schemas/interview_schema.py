"""Pydantic validation schemas for the Mock Interview Engine.
"""

from typing import Optional, Union
from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    """Payload to start a mock interview session."""
    match_id: Union[int, str] = Field(..., description="The ID of the ResumeMatch record.")


class InterviewStartResponse(BaseModel):
    """Response containing session information and the initial question."""
    session_id: str = Field(..., description="The UUID of the created interview session.")
    current_question: str = Field(..., description="The first interview question.")


class AnswerSubmitRequest(BaseModel):
    """Payload to submit a candidate answer to the current question."""
    session_id: str = Field(..., description="The UUID of the active interview session.")
    answer: str = Field(..., description="The raw transcript or text of the candidate's answer.")


class AnswerSubmitResponse(BaseModel):
    """Response returned after submitting an answer, either providing the next question or completion status."""
    is_finished: bool = Field(False, description="Whether the interview session has completed.")
    next_question: Optional[str] = Field(None, description="The next interview question, if available.")
    status: Optional[str] = Field(None, description="Current session status (e.g. 'completed' if the interview ended).")


class InterviewEndRequest(BaseModel):
    """Payload to manually terminate an interview session early."""
    session_id: str = Field(..., description="The UUID of the interview session to complete.")
