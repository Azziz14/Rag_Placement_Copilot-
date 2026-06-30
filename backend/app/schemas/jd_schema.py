"""Pydantic schemas for the JobDescription model.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class JobDescriptionBase(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience_required: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    technologies: Optional[List[str]] = None


class JobDescriptionCreate(JobDescriptionBase):
    raw_text: str
    user_id: str


class JobDescriptionResponse(JobDescriptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    raw_text: str
    created_at: datetime


class JobDescriptionTextAnalyze(BaseModel):
    raw_text: str
