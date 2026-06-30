"""Pydantic validation schemas for the Improvement Roadmap Engine.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RoadmapRequest(BaseModel):
    """Payload to generate an improvement roadmap for a mock interview session."""
    session_id: str = Field(..., description="The UUID of the completed interview session.")


class RoadmapResponse(BaseModel):
    """Aggregated improvement roadmap response for a session."""
    id: str = Field(..., description="The UUID of the roadmap record.")
    session_id: str = Field(..., description="The UUID of the interview session.")
    technical_plan: List[Dict[str, Any]] = Field(default=[], description="Technical preparation study plan with short, medium, and long-term goals.")
    dsa_plan: List[Dict[str, Any]] = Field(default=[], description="Data Structures & Algorithms preparation study plan with short, medium, and long-term goals.")
    behavioral_plan: List[Dict[str, Any]] = Field(default=[], description="Behavioral preparation study plan with short, medium, and long-term goals.")
    resource_recommendations: List[Dict[str, Any]] = Field(default=[], description="Recommended resources (articles, courses, documentation, exercises).")
    created_at: datetime = Field(..., description="Timestamp of when the roadmap was generated.")

    class Config:
        from_attributes = True
