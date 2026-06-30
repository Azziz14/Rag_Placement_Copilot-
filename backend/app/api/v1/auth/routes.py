"""Authentication routers and endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    SignUpRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    SyncUserRequest
)
from app.services.auth_service import auth_service
from app.api.v1.auth.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_or_create_user(db: Session, user_id: str, email: str, full_name: str = None) -> User:
    """Helper to get user or create if they do not exist in PostgreSQL."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        db_user = User(
            id=user_id,
            email=email,
            full_name=full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    elif full_name and db_user.full_name != full_name:
        db_user.full_name = full_name
        db.commit()
        db.refresh(db_user)
    return db_user


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    """Registers a new user in Supabase and synchronizes them to PostgreSQL."""
    try:
        signup_response = auth_service.sign_up(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supabase signup failed: {str(e)}"
        )

    user_info = signup_response.user
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup succeeded but no user details were returned"
        )

    # Sync to local PostgreSQL
    db_user = get_or_create_user(
        db=db,
        user_id=user_info.id,
        email=user_info.email,
        full_name=payload.full_name
    )
    return db_user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Logs in user in Supabase, returns JWT token and syncs the user to PostgreSQL."""
    try:
        login_response = auth_service.sign_in(
            email=str(payload.email),
            password=payload.password
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )

    session = login_response.session
    user_info = login_response.user
    if not session or not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or session not established"
        )

    # Sync/Ensure user exists locally
    full_name = user_info.user_metadata.get("full_name") if user_info.user_metadata else None
    db_user = get_or_create_user(
        db=db,
        user_id=user_info.id,
        email=user_info.email,
        full_name=full_name
    )

    return TokenResponse(
        access_token=session.access_token,
        user=UserResponse.model_validate(db_user)
    )


@router.post("/sync", response_model=UserResponse)
async def sync_supabase_user(payload: SyncUserRequest, db: Session = Depends(get_db)):
    """Verifies a Supabase JWT token and synchronizes the user to PostgreSQL."""
    try:
        decoded_payload = auth_service.verify_token(payload.access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    user_id = decoded_payload.get("sub")
    email = decoded_payload.get("email")
    metadata = decoded_payload.get("user_metadata", {})
    full_name = metadata.get("full_name") if isinstance(metadata, dict) else None

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token payload missing required fields (sub, email)"
        )

    db_user = get_or_create_user(
        db=db,
        user_id=user_id,
        email=email,
        full_name=full_name
    )
    return db_user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Protected endpoint to retrieve the current user's profile."""
    return current_user
