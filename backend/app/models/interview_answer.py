"""SQLAlchemy database model for InterviewAnswer.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class InterviewAnswer(Base):
    """InterviewAnswer model corresponding to the 'interview_answers' table."""
    __tablename__ = "interview_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    category = Column(String, nullable=False)  # 'technical', 'project', 'behavioral', 'dsa'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("InterviewSession", back_populates="answers")
