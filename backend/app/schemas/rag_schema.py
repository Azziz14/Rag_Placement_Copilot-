"""Pydantic schemas for the RAG Retrieval Engine.
"""

from typing import List, Dict, Any
from pydantic import BaseModel


class RAGRetrieveRequest(BaseModel):
    """Schema for requesting context retrieval."""
    match_id: str


class RAGContextItem(BaseModel):
    """Schema representing a single retrieved document chunk."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class RAGRetrieveResponse(BaseModel):
    """Schema for the aggregated RAG retrieval response."""
    role_context: List[RAGContextItem]
    company_context: List[RAGContextItem]
    missing_skill_context: List[RAGContextItem]
    behavioral_context: List[RAGContextItem]
    dsa_context: List[RAGContextItem]
