"""Pydantic schemas for the Progress Tracking Dashboard module.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional


class ScoreTrendItem(BaseModel):
    """Pydantic model representing a single point in the user's score trend."""
    session_id: str
    date: str
    average_score: float


class RoadmapCompletionDetail(BaseModel):
    """Pydantic model representing roadmap completion details."""
    completed_goals: int
    total_goals: int
    completion_percentage: float


class ProgressSnapshotResponse(BaseModel):
    """Pydantic schema for database progress snapshots and endpoint output."""
    id: str
    user_id: str
    overall_progress: float
    score_trend: List[ScoreTrendItem]
    improved_areas: List[str]
    persistent_weaknesses: List[str]
    roadmap_completion: RoadmapCompletionDetail
    created_at: datetime

    class Config:
        from_attributes = True


class JDScoreHistoryItem(BaseModel):
    match_id: str
    resume_id: str
    job_description_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    match_score: float
    matched_skills_count: int
    missing_skills_count: int
    created_at: datetime


class SessionScoreHistoryItem(BaseModel):
    session_id: str
    match_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    status: str
    average_score: float
    evaluation_count: int
    started_at: datetime
    ended_at: Optional[datetime] = None


class ScoreHistoryResponse(BaseModel):
    jd_scores: List[JDScoreHistoryItem]
    session_scores: List[SessionScoreHistoryItem]
