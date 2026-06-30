"""FastAPI routing module for the Personalized Question Generator.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.resume_match import ResumeMatch
from app.models.interview_session import InterviewSession
from app.schemas.question_schema import QuestionGenerationRequest, QuestionGenerationResponse
from app.services.rag_service import rag_service
from app.services.question_service import question_service

router = APIRouter(prefix="/questions", tags=["Personalized Question Generator"])


def load_previous_questions(db: Session, user_id: str, match_id: str) -> list[str]:
    """Loads previously asked questions so new previews avoid repeats."""
    current_match = db.query(ResumeMatch).filter(
        ResumeMatch.id == str(match_id),
        ResumeMatch.user_id == user_id
    ).first()
    related_match_ids = [str(match_id)]
    if current_match:
        related_matches = db.query(ResumeMatch).filter(
            ResumeMatch.user_id == user_id,
            ResumeMatch.resume_id == current_match.resume_id,
            ResumeMatch.job_description_id == current_match.job_description_id
        ).all()
        related_match_ids = [match.id for match in related_matches]

    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.match_id.in_(related_match_ids),
        InterviewSession.questions.isnot(None)
    ).order_by(InterviewSession.started_at.desc()).limit(10).all()

    previous_questions = []
    for session in sessions:
        try:
            cached_questions = json.loads(session.questions or "[]")
            for item in cached_questions:
                if isinstance(item, (list, tuple)) and item:
                    previous_questions.append(str(item[0]))
                elif isinstance(item, str):
                    previous_questions.append(item)
        except Exception:
            continue
    return previous_questions


async def get_current_user_dynamic(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency helper that dynamically resolves security get_current_user to avoid circular imports."""
    from fastapi.security import HTTPBearer
    from app.api.v1.auth.security import get_current_user
    
    # Extract authorization header manually to pass to credentials check
    auth_header = request.headers.get("Authorization")
    if not auth_header:
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Not authenticated",
             headers={"WWW-Authenticate": "Bearer"},
         )
         
    # Parse Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Invalid authentication credentials",
             headers={"WWW-Authenticate": "Bearer"},
         )
         
    from fastapi.security.http import HTTPAuthorizationCredentials
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=parts[1])
    return await get_current_user(credentials=credentials, db=db)


@router.post("/generate", response_model=QuestionGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_questions(
    payload: QuestionGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dynamic)
):
    """Generates personalized interview questions based on match analysis and retrieved vector store contexts.
    
    Verifies that the match record and associated documents belong to the authenticated user,
    fetches RAG-based context, calls the question generation service, and returns structured results.
    """
    # 1. Fetch and verify match record ownership
    match = db.query(ResumeMatch).filter(
        ResumeMatch.id == payload.match_id,
        ResumeMatch.user_id == current_user.id
    ).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match record with ID {payload.match_id} not found or unauthorized."
        )

    # 2. Fetch associated Resume
    resume = db.query(Resume).filter(
        Resume.id == match.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume document associated with this match analysis not found."
        )

    # 3. Fetch associated Job Description
    jd = db.query(JobDescription).filter(
        JobDescription.id == match.job_description_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job Description document associated with this match analysis not found."
        )

    # 4. Pull RAG context using the RAG Service
    try:
        rag_context = rag_service.retrieve_all_context(
            db=db,
            user_id=current_user.id,
            match_id=payload.match_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve vector store context: {str(e)}"
        )

    # 5. Generate categorized questions
    try:
        categorized_questions = question_service.generate_questions(
            resume=resume,
            jd=jd,
            match=match,
            rag_context=rag_context,
            previous_questions=load_previous_questions(db, current_user.id, str(payload.match_id))
        )
        return categorized_questions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )
