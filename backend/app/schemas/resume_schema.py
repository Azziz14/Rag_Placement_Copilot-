"""Pydantic schemas for the Resume model.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class ResumeBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    technologies: Optional[List[str]] = None


class ResumeCreate(ResumeBase):
    original_filename: str
    extracted_text: str
    user_id: str


class ResumeResponse(ResumeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    original_filename: str
    extracted_text: str
    created_at: datetime
