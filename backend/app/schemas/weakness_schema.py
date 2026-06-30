"""Pydantic validation schemas for the Weakness Analysis Engine.
"""

from datetime import datetime
from typing import List, Union, Dict, Any
from pydantic import BaseModel, Field


class WeaknessAnalysisRequest(BaseModel):
    """Payload to trigger weakness analysis for a mock interview session."""
    session_id: str = Field(..., description="The UUID of the completed interview session.")


class WeaknessAnalysisResponse(BaseModel):
    """Aggregated weakness analysis response for a session."""
    id: str = Field(..., description="The UUID of the weakness analysis record.")
    session_id: str = Field(..., description="The UUID of the interview session.")
    technical_weaknesses: List[Union[str, Dict[str, Any]]] = Field(default=[], description="List of technical weakness patterns and details.")
    behavioral_weaknesses: List[Union[str, Dict[str, Any]]] = Field(default=[], description="List of behavioral weakness patterns and details.")
    dsa_weaknesses: List[Union[str, Dict[str, Any]]] = Field(default=[], description="List of DSA weakness patterns and details.")
    communication_weaknesses: List[Union[str, Dict[str, Any]]] = Field(default=[], description="List of communication weakness patterns and details.")
    priority_areas: List[Union[str, Dict[str, Any]]] = Field(default=[], description="Ranked list of weaknesses that require immediate focus.")
    created_at: datetime = Field(..., description="Timestamp of when the analysis was generated.")

    class Config:
        from_attributes = True
