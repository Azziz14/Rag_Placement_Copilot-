"""SQLAlchemy database model for ImprovementRoadmap.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ImprovementRoadmap(Base):
    """ImprovementRoadmap model corresponding to the 'improvement_roadmaps' table."""
    __tablename__ = "improvement_roadmaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    technical_plan = Column(JSON, nullable=True)  # JSON structure containing goals (short, medium, long term)
    dsa_plan = Column(JSON, nullable=True)  # JSON structure containing goals (short, medium, long term)
    behavioral_plan = Column(JSON, nullable=True)  # JSON structure containing goals (short, medium, long term)
    resource_recommendations = Column(JSON, nullable=True)  # JSON structure with recommended articles/videos/docs
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("InterviewSession")
