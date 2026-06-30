"""Pydantic schemas for the Resume Tailoring feature.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TailorResumeRequest(BaseModel):
    resume_id: str
    jd_id: str
    target_role: str
    focus_areas: Optional[List[str]] = Field(default=None)
    exclude_sections: Optional[List[str]] = Field(default=None)
    tone: str
    preserve_format: bool = True
    custom_instructions: Optional[str] = ""


class TailorResumeResponse(BaseModel):
    tailored_resume_id: str
    original_score: float
    improved_score: float
    changed_sections: List[str]
    download_url: str
