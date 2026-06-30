"""FastAPI routing module for the Adaptive Interview Loop.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.adaptive_schema import AdaptiveGenerateRequest, AdaptiveProfileResponse
from app.services.adaptive_service import adaptive_service

router = APIRouter(prefix="/adaptive", tags=["Adaptive Interview Loop"])


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


@router.post("/generate", response_model=AdaptiveProfileResponse, status_code=status.HTTP_200_OK)
async def generate_adaptive_profile(
    payload: AdaptiveGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Generates an adaptive interview and study preparation profile.

    Aggregates historical mock interview sessions, evaluations, weakness analyses,
    improvement roadmaps, and progress snapshots to establish next focus areas,
    adjust interview difficulties, prioritize question targets, and recommend 
    future interview formats.
    """
    if current_user.id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to generate an adaptive profile for another user."
        )

    try:
        profile = adaptive_service.generate_adaptive_profile(
            db=db, 
            user_id=payload.user_id,
            force_refresh=payload.force_refresh
        )
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during adaptive profile generation: {str(e)}"
        )
