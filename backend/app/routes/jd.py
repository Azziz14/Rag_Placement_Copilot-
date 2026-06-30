"""Job Description routing module.
"""

import os
import shutil
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.job_description import JobDescription
from app.schemas.jd_schema import JobDescriptionResponse, JobDescriptionTextAnalyze
from app.services.jd_parser import extract_text, parse_jd_text
from app.api.v1.auth.security import get_current_user

router = APIRouter(prefix="/jd", tags=["Job Description Analyzer"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit


@router.post("/upload", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def upload_job_description(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uploads a job description file (PDF/DOCX), extracts and parses its contents,
    stores the structured job description in the database, and returns the response.
    """
    allowed_extensions = {".pdf", ".docx"}

    # 1. Sanitize original filename to prevent path traversal
    filename = os.path.basename(file.filename or "job_description")
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF and DOCX files are allowed, but got: {ext}"
        )

    # 2. File size validation
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read file size: {str(e)}"
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size limit of 10MB (file size: {file_size} bytes)."
        )

    # Write to a temporary file safely
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save uploaded file temporarily: {str(e)}"
        )

    try:
        # Extract text from temp file
        raw_text = extract_text(temp_path)
        
        # Parse the job description text
        parsed_data = parse_jd_text(raw_text)

        # Create model instance
        db_jd = JobDescription(
            user_id=current_user.id,
            job_title=parsed_data.get("job_title") or "Job Position",
            company_name=parsed_data.get("company_name"),
            raw_text=raw_text,
            required_skills=parsed_data.get("required_skills") or [],
            preferred_skills=parsed_data.get("preferred_skills") or [],
            experience_required=parsed_data.get("experience_required"),
            responsibilities=parsed_data.get("responsibilities") or [],
            qualifications=parsed_data.get("qualifications") or [],
            technologies=parsed_data.get("technologies") or []
        )

        db.add(db_jd)
        db.commit()
        db.refresh(db_jd)

        return db_jd

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing or saving job description: {str(e)}"
        )
    finally:
        # Safe cleanup of temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.post("/analyze-text", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def analyze_jd_text(
    payload: JobDescriptionTextAnalyze,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyzes raw text of a job description directly, stores the structured
    details in the database, and returns the response.
    """
    raw_text = payload.raw_text
    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty."
        )

    try:
        parsed_data = parse_jd_text(raw_text)

        # Create model instance
        db_jd = JobDescription(
            user_id=current_user.id,
            job_title=parsed_data.get("job_title") or "Job Position",
            company_name=parsed_data.get("company_name"),
            raw_text=raw_text,
            required_skills=parsed_data.get("required_skills") or [],
            preferred_skills=parsed_data.get("preferred_skills") or [],
            experience_required=parsed_data.get("experience_required"),
            responsibilities=parsed_data.get("responsibilities") or [],
            qualifications=parsed_data.get("qualifications") or [],
            technologies=parsed_data.get("technologies") or []
        )

        db.add(db_jd)
        db.commit()
        db.refresh(db_jd)

        return db_jd

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing or saving job description text: {str(e)}"
        )
