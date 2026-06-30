"""Pydantic schemas for the Resume-JD Matcher.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MatchRequest(BaseModel):
    """Schema for requesting a resume match analysis."""
    resume_id: str
    job_description_id: str


class MatchResponse(BaseModel):
    """Schema representing a match result."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    resume_id: str
    job_description_id: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    matched_technologies: List[str]
    missing_technologies: List[str]
    strong_areas: List[str]
    improvement_areas: List[str]
    created_at: datetime
