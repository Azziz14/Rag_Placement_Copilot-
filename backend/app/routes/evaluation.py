"""FastAPI routing module for the Answer Evaluation Engine.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.evaluation_schema import EvaluationRequest, SessionEvaluationResponse
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/evaluation", tags=["Answer Evaluation Engine"])


async def get_current_user_dynamic(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency helper that dynamically resolves security get_current_user to avoid circular imports."""
    from app.api.v1.auth.security import get_current_user
    from fastapi.security.http import HTTPAuthorizationCredentials
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Not authenticated",
             headers={"WWW-Authenticate": "Bearer"},
         )
         
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Invalid authentication credentials",
             headers={"WWW-Authenticate": "Bearer"},
         )
         
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=parts[1])
    return await get_current_user(credentials=credentials, db=db)


@router.post("/analyze", response_model=SessionEvaluationResponse, status_code=status.HTTP_200_OK)
async def analyze_session(
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Evaluates the candidate's answers from a completed mock interview session.

    Retrieves all interview answers, scores them on relevance, depth, clarity,
    technical accuracy, and confidence using LLM or rule-based heuristics, 
    persists the results, and returns the evaluation reports.
    """
    try:
        results = evaluation_service.evaluate_session_answers(
            db=db,
            user_id=current_user.id,
            session_id=payload.session_id
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during answer evaluation: {str(e)}"
        )
