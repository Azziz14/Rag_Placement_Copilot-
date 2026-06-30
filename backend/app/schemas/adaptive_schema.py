"""Pydantic validation schemas for the Adaptive Interview Loop module.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AdaptiveGenerateRequest(BaseModel):
    """Payload to trigger generation of an adaptive preparation profile."""
    user_id: str = Field(..., description="The UUID of the authenticated user.")
    force_refresh: Optional[bool] = Field(default=False, description="Bypass cache and force regeneration.")


class AdaptiveProfileResponse(BaseModel):
    """Adaptive preparation profile details returned to the frontend."""
    id: str = Field(..., description="The UUID of the adaptive profile.")
    user_id: str = Field(..., description="The UUID of the user.")
    next_focus_areas: List[Dict[str, Any]] = Field(default=[], description="Identified areas for next interviews (e.g. subject, subtopics, level of focus).")
    difficulty_adjustments: List[Dict[str, Any]] = Field(default=[], description="Recommended adjustments to difficulty settings for specific sections.")
    priority_questions: List[Dict[str, Any]] = Field(default=[], description="Prioritized questions or question templates to present next.")
    recommended_interview_type: str = Field(..., description="Type of mock interview recommended (e.g. Technical Focus, Behavioral Focus, System Design, Balanced).")
    created_at: datetime = Field(..., description="Timestamp of when this profile was generated.")

    class Config:
        from_attributes = True
