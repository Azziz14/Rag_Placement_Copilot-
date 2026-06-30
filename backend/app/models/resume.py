"""SQLAlchemy database model for Resume.

Represents the parsed resume information of a user.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Resume(Base):
    """Resume model corresponding to the 'resumes' table in PostgreSQL."""
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    original_filename = Column(String, nullable=False)
    extracted_text = Column(String, nullable=False)
    skills = Column(JSON, nullable=True)  # List of strings
    education = Column(JSON, nullable=True)  # List of dicts/objects
    experience = Column(JSON, nullable=True)  # List of dicts/objects
    projects = Column(JSON, nullable=True)  # List of dicts/objects
    certifications = Column(JSON, nullable=True)  # List of strings
    technologies = Column(JSON, nullable=True)  # List of strings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="resumes")
