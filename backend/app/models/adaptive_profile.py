"""SQLAlchemy database model for AdaptiveProfile.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class AdaptiveProfile(Base):
    """AdaptiveProfile model corresponding to the 'adaptive_profiles' table."""
    __tablename__ = "adaptive_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    next_focus_areas = Column(JSON, nullable=True)  # List of Dict/String
    difficulty_adjustments = Column(JSON, nullable=True)  # Dict
    priority_questions = Column(JSON, nullable=True)  # List of Dict/String
    recommended_interview_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
