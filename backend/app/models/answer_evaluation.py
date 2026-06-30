"""SQLAlchemy database model for AnswerEvaluation.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class AnswerEvaluation(Base):
    """AnswerEvaluation model corresponding to the 'answer_evaluations' table."""
    __tablename__ = "answer_evaluations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    answer_id = Column(String, ForeignKey("interview_answers.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Integer, nullable=False)
    relevance_score = Column(Integer, nullable=False)
    depth_score = Column(Integer, nullable=False)
    clarity_score = Column(Integer, nullable=False)
    technical_accuracy_score = Column(Integer, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    strengths = Column(JSON, nullable=True)  # List of strings
    weaknesses = Column(JSON, nullable=True)  # List of strings
    suggestions = Column(JSON, nullable=True)  # List of strings
    key_phrases = Column(JSON, nullable=True)  # List of strings
    matched_key_phrases = Column(JSON, nullable=True)  # List of strings
    missing_key_phrases = Column(JSON, nullable=True)  # List of strings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("InterviewSession")
    answer = relationship("InterviewAnswer")
