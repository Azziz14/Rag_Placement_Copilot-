"""SQLAlchemy database model for WeaknessAnalysis.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class WeaknessAnalysis(Base):
    """WeaknessAnalysis model corresponding to the 'weakness_analysis' table."""
    __tablename__ = "weakness_analysis"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    technical_weaknesses = Column(JSON, nullable=True)  # List of strings or dicts
    behavioral_weaknesses = Column(JSON, nullable=True)  # List of strings or dicts
    dsa_weaknesses = Column(JSON, nullable=True)  # List of strings or dicts
    communication_weaknesses = Column(JSON, nullable=True)  # List of strings or dicts
    priority_areas = Column(JSON, nullable=True)  # List of strings or dicts
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("InterviewSession")
