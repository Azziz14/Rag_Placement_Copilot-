"""FastAPI routing module for the Mock Interview Engine.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.interview_schema import (
    InterviewStartRequest,
    InterviewStartResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    InterviewEndRequest
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["Mock Interview Engine"])
interview_service = InterviewService()


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


@router.post("/start", response_model=InterviewStartResponse, status_code=status.HTTP_201_CREATED)
async def start_mock_interview(
    payload: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Initializes a new mock interview session, locking questions sequence and returning the first question."""
    try:
        session_id, first_question = interview_service.start_interview(
            db=db,
            user_id=current_user.id,
            match_id=payload.match_id
        )
        return {
            "session_id": session_id,
            "current_question": first_question
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while starting the interview: {str(e)}"
        )


@router.post("/answer", response_model=AnswerSubmitResponse, status_code=status.HTTP_200_OK)
async def submit_answer(
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Submits the candidate's answer for the current question and advances to the next question."""
    try:
        result = interview_service.save_answer(
            db=db,
            user_id=current_user.id,
            session_id=payload.session_id,
            answer_text=payload.answer
        )
        return result
    except ValueError as e:
        # Client validation error (e.g. empty answer, session completed)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while saving the answer: {str(e)}"
        )


@router.post("/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_mock_interview(
    payload: InterviewEndRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Manually terminates an ongoing mock interview session, locking it from further submissions."""
    try:
        interview_service.end_interview(
            db=db,
            user_id=current_user.id,
            session_id=payload.session_id
        )
        return
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while ending the interview: {str(e)}"
        )
