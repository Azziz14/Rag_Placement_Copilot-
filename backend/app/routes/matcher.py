"""Resume-JD Matcher routing module.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.matcher_schema import MatchRequest, MatchResponse
from app.services.matcher_service import matcher_service
from app.api.v1.auth.security import get_current_user

router = APIRouter(prefix="/match", tags=["Resume-JD Matcher"])


@router.post("/analyze", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def analyze_match(
    payload: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compares a candidate's resume with a job description.
    
    Validates ownership of both documents, calculates matching scores,
    persists the analysis to the database, and returns the match insights.
    """
    try:
        db_match = matcher_service.perform_match_analysis(
            db=db,
            user_id=current_user.id,
            resume_id=payload.resume_id,
            job_description_id=payload.job_description_id
        )
        return db_match
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {str(e)}"
        )
