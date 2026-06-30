"""FastAPI routing module for the Progress Tracking Dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.progress_schema import ProgressSnapshotResponse, ScoreHistoryResponse
from app.services.progress_service import progress_service

router = APIRouter(prefix="/progress", tags=["Progress Dashboard"])


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


@router.get("/dashboard/{user_id}", response_model=ProgressSnapshotResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_snapshot(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Retrieves progress tracking dashboard metrics and stores a snapshot.

    Aggregates historical mock interview sessions, evaluations, weakness analyses,
    improvement roadmaps, and resume matches to build trend analysis.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access another user's progress dashboard."
        )

    try:
        snapshot = progress_service.get_or_create_dashboard_snapshot(db=db, user_id=user_id)
        return snapshot
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during dashboard generation: {str(e)}"
        )


@router.get("/history/{user_id}", response_model=ScoreHistoryResponse, status_code=status.HTTP_200_OK)
async def get_score_history(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Retrieves historical scores across JD analyses and interview sessions."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access another user's score history."
        )

    try:
        return progress_service.get_score_history(db=db, user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during score history retrieval: {str(e)}"
        )
