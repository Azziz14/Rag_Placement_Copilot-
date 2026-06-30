"""SQLAlchemy database model for ResumeMatch.

Represents the computed matches between a resume and a job description.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class ResumeMatch(Base):
    """ResumeMatch model corresponding to the 'resume_matches' table in PostgreSQL/SQLite."""
    __tablename__ = "resume_matches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    match_score = Column(Float, nullable=False)
    matched_skills = Column(JSON, nullable=True)  # List of strings
    missing_skills = Column(JSON, nullable=True)  # List of strings
    matched_technologies = Column(JSON, nullable=True)  # List of strings
    missing_technologies = Column(JSON, nullable=True)  # List of strings
    strong_areas = Column(JSON, nullable=True)  # List of strings
    improvement_areas = Column(JSON, nullable=True)  # List of strings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
    resume = relationship("Resume")
    job_description = relationship("JobDescription")
