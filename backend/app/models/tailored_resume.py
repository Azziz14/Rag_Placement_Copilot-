"""SQLAlchemy database model for TailoredResume.

Represents a resume that has been tailored to a specific job description.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class TailoredResume(Base):
    """TailoredResume model corresponding to the 'tailored_resumes' table."""
    __tablename__ = "tailored_resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    jd_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    original_score = Column(Float, nullable=False)
    improved_score = Column(Float, nullable=False)
    preferences_json = Column(JSON, nullable=False)
    output_file_path = Column(String, nullable=False)
    format_type = Column(String, nullable=False)  # 'pdf' or 'docx'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
    resume = relationship("Resume")
    job_description = relationship("JobDescription")
