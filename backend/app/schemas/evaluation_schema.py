"""Pydantic validation schemas for the Answer Evaluation Engine.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    """Payload to request evaluation for an interview session."""
    session_id: str = Field(..., description="The UUID of the completed interview session.")


class AnswerEvaluationDetail(BaseModel):
    """Detailed evaluation result for a single question-answer pair."""
    id: str = Field(..., description="The UUID of the evaluation record.")
    session_id: str = Field(..., description="The UUID of the interview session.")
    answer_id: str = Field(..., description="The UUID of the associated interview answer.")
    question: str = Field(..., description="The question that was asked.")
    answer: str = Field(..., description="The candidate's response.")
    category: str = Field(..., description="The question category (technical, project, behavioral, dsa).")
    overall_score: int = Field(..., ge=0, le=100, description="Overall score for the answer.")
    relevance_score: int = Field(..., ge=0, le=100, description="Relevance score.")
    depth_score: int = Field(..., ge=0, le=100, description="Depth score.")
    clarity_score: int = Field(..., ge=0, le=100, description="Clarity score.")
    technical_accuracy_score: int = Field(..., ge=0, le=100, description="Technical accuracy score.")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score.")
    strengths: List[str] = Field(default=[], description="List of strengths in the answer.")
    weaknesses: List[str] = Field(default=[], description="List of weaknesses or gaps in the answer.")
    suggestions: List[str] = Field(default=[], description="List of actionable suggestions for improvement.")
    key_phrases: List[str] = Field(default=[], description="List of critical keywords or concepts expected in the answer.")
    matched_key_phrases: List[str] = Field(default=[], description="List of keywords successfully covered in the answer.")
    missing_key_phrases: List[str] = Field(default=[], description="List of keywords candidate missed in the answer.")
    created_at: datetime = Field(..., description="Timestamp of when the evaluation was created.")

    class Config:
        from_attributes = True


class SessionEvaluationResponse(BaseModel):
    """Overall evaluation response for a mock interview session."""
    session_id: str = Field(..., description="The UUID of the interview session.")
    evaluations: List[AnswerEvaluationDetail] = Field(default=[], description="List of answer evaluations.")
