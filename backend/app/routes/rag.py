"""RAG Retrieval Engine routing module.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.rag_schema import RAGRetrieveRequest, RAGRetrieveResponse
from app.services.rag_service import rag_service
from app.api.v1.auth.security import get_current_user

router = APIRouter(prefix="/rag", tags=["RAG Retrieval Engine"])


@router.post("/retrieve", response_model=RAGRetrieveResponse, status_code=status.HTTP_200_OK)
async def retrieve_rag_context(
    payload: RAGRetrieveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves relevant context chunks from the vector database based on matching results.
    
    Checks ownership, builds queries, pulls matching documents from ChromaDB,
    and returns aggregated contexts structured by DSA, behavioral, company, role, and gaps.
    """
    try:
        context_data = rag_service.retrieve_all_context(
            db=db,
            user_id=current_user.id,
            match_id=payload.match_id
        )
        return context_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during context retrieval: {str(e)}"
        )
