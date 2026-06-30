"""SQLAlchemy database model for JobDescription.

Represents the parsed job description information linked to a user.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class JobDescription(Base):
    """JobDescription model corresponding to the 'job_descriptions' table in PostgreSQL."""
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    raw_text = Column(String, nullable=False)
    required_skills = Column(JSON, nullable=True)  # List of strings
    preferred_skills = Column(JSON, nullable=True)  # List of strings
    experience_required = Column(String, nullable=True)
    responsibilities = Column(JSON, nullable=True)  # List of strings
    qualifications = Column(JSON, nullable=True)  # List of strings
    technologies = Column(JSON, nullable=True)  # List of strings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="job_descriptions")
