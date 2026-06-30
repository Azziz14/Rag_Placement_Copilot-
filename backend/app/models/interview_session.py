"""SQLAlchemy database model for InterviewSession.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class InterviewSession(Base):
    """InterviewSession model corresponding to the 'interview_sessions' table."""
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_id = Column(String, ForeignKey("resume_matches.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="started", nullable=False)  # 'started', 'completed'
    current_question_index = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    questions = Column(String, nullable=True)  # JSON-serialized list of (question_text, category)

    # Relationships
    user = relationship("User")
    resume_match = relationship("ResumeMatch")
    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")
