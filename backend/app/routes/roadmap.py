"""FastAPI routing module for the Personalized Improvement Roadmap Engine.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.roadmap_schema import RoadmapRequest, RoadmapResponse
from app.services.roadmap_service import roadmap_service

router = APIRouter(prefix="/roadmap", tags=["Improvement Roadmap Engine"])


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


@router.post("/generate", response_model=RoadmapResponse, status_code=status.HTTP_200_OK)
async def generate_roadmap(
    payload: RoadmapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Generates a personalized study roadmap for a mock interview session.

    Retrieves weakness analysis results, Resume-JD Match gaps, and relevant RAG study context.
    Produces short, medium, and long term plans for technical, behavioral, and DSA areas,
    recommends specific learning resources, stores the roadmap, and returns it.
    """
    try:
        results = roadmap_service.generate_roadmap(
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
            detail=f"An unexpected error occurred during roadmap generation: {str(e)}"
        )
