"""Resume routing module.
"""

import os
import shutil
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.schemas.resume_schema import ResumeResponse
from app.services.resume_parser import parse_resume_file
from app.api.v1.auth.security import get_current_user

router = APIRouter(prefix="/resume", tags=["Resume Parser"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uploads a resume file (PDF/DOCX), extracts and parses its contents,
    stores the structured resume in the database, and returns the response.
    """
    allowed_extensions = {".pdf", ".docx"}
    
    # 1. Sanitize original filename to prevent path traversal
    filename = os.path.basename(file.filename or "resume")
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF and DOCX files are allowed, but got: {ext}"
        )
        
    # 2. File size validation to prevent denial of service (DoS)
    # Seek to end to check size, then seek back to start
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
        # Parse resume file contents using refactored service function
        parsed_data = parse_resume_file(temp_path, filename)
        
        # 3. Default JSON list fields to empty lists if None/empty
        skills = parsed_data.get("skills") or []
        education = parsed_data.get("education") or []
        experience = parsed_data.get("experience") or []
        projects = parsed_data.get("projects") or []
        certifications = parsed_data.get("certifications") or []
        technologies = parsed_data.get("technologies") or []
        
        # Save parsed resume to Database linked to the current user
        db_resume = Resume(
            user_id=current_user.id,
            original_filename=parsed_data["original_filename"],
            extracted_text=parsed_data["extracted_text"],
            full_name=parsed_data.get("full_name") or "",
            email=parsed_data.get("email") or "",
            phone=parsed_data.get("phone") or "",
            skills=skills,
            education=education,
            experience=experience,
            projects=projects,
            certifications=certifications,
            technologies=technologies
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        # Copy to uploads directory for tailoring engine format preservation
        uploads_dir = os.path.join(os.getcwd(), "uploads", "resumes")
        os.makedirs(uploads_dir, exist_ok=True)
        permanent_path = os.path.join(uploads_dir, f"{db_resume.id}{ext}")
        shutil.copy2(temp_path, permanent_path)
        
        return db_resume
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing or saving resume: {str(e)}"
        )
    finally:
        # Safe cleanup of temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
