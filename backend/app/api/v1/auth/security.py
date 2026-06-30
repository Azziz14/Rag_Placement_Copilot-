"""Security dependencies for protecting FastAPI routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to verify the Supabase JWT and retrieve the PostgreSQL User.
    
    Raises 401 Unauthorized if verification fails or user is not found.
    """
    token = credentials.credentials
    try:
        payload = auth_service.verify_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Payload contains 'sub' as user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing sub (user ID)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retrieve user from PostgreSQL database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Auto-sync user to PostgreSQL
        email = payload.get("email")
        metadata = payload.get("user_metadata", {}) or {}
        full_name = metadata.get("full_name") if isinstance(metadata, dict) else None
        
        user = User(
            id=user_id,
            email=email,
            full_name=full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
