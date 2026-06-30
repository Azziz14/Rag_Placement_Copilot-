"""SQLAlchemy database model for ProgressSnapshot.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProgressSnapshot(Base):
    """ProgressSnapshot model corresponding to the 'progress_snapshots' table."""
    __tablename__ = "progress_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    overall_progress = Column(Float, nullable=False)
    score_trend = Column(JSON, nullable=True)  # List of Dict
    improved_areas = Column(JSON, nullable=True)  # List of String
    persistent_weaknesses = Column(JSON, nullable=True)  # List of String
    roadmap_completion = Column(JSON, nullable=True)  # Dict with completed_goals, total_goals, completion_percentage
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
