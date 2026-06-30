import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class MatchScoreVersion(Base):
    """Model to store historical resume match scores for version tracking."""
    __tablename__ = "match_score_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    jd_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    resume = relationship("Resume")
    job_description = relationship("JobDescription")
