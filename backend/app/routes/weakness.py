"""FastAPI routing module for the Weakness Analysis Engine.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.weakness_schema import WeaknessAnalysisRequest, WeaknessAnalysisResponse
from app.services.weakness_service import weakness_service

router = APIRouter(prefix="/weakness", tags=["Weakness Analysis Engine"])


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


@router.post("/analyze", response_model=WeaknessAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_weaknesses(
    payload: WeaknessAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Aggregates and prioritizes interview answer weaknesses across a mock interview session.

    Retrieves mock evaluations and ResumeMatch skill gaps, runs pattern-based aggregation
    to group technical, behavioral, DSA, and communication weaknesses, ranks focus areas,
    stores the results, and returns the aggregated analysis JSON.
    """
    try:
        results = weakness_service.analyze_session_weaknesses(
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
            detail=f"An unexpected error occurred during weakness analysis: {str(e)}"
        )
