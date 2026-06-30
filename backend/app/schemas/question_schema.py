"""Pydantic schemas for the Personalized Question Generator.
"""

from typing import List, Union
from pydantic import BaseModel, Field


class QuestionGenerationRequest(BaseModel):
    """Request schema to trigger question generation based on a resume-JD match ID."""
    match_id: Union[int, str] = Field(..., description="The ID of the ResumeMatch record (supports UUID strings and integers).")


class QuestionGenerationResponse(BaseModel):
    """Structured response schema representing categorized generated interview questions."""
    technical_questions: List[str] = Field(
        default_factory=list,
        description="Questions focusing on technical concepts, matched/missing skills, and role-specific architecture."
    )
    project_questions: List[str] = Field(
        default_factory=list,
        description="Questions probing into candidate projects, technologies used, and engineering choices."
    )
    behavioral_questions: List[str] = Field(
        default_factory=list,
        description="Questions assessing company values alignment, team collaboration, and behavioral scenarios."
    )
    dsa_questions: List[str] = Field(
        default_factory=list,
        description="Coding, data structures, and algorithmic questions tailored to the role."
    )
