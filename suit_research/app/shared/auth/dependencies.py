"""Shared authentication dependencies for Suit Research."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, AuthType

# Import shared auth service
try:
    from app.shared.auth.unified_auth_service import UnifiedAuthService
except ImportError:
    # Fallback for local development
    from app.services.auth.unified_auth_service import UnifiedAuthService


security = HTTPBearer(auto_error=False)
auth_service = UnifiedAuthService()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user (required)."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user (optional)."""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    
    return user


async def require_email_auth(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have email authentication."""
    if not current_user.has_email_auth():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email authentication required"
        )
    return current_user


async def require_wallet_auth(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have wallet authentication."""
    if not current_user.has_wallet_auth():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wallet authentication required"
        )
    return current_user


async def require_verified_email(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have verified email."""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


async def require_verified_wallet(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have verified wallet."""
    if not current_user.wallet_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wallet verification required"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to be an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_analyst_or_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to be an analyst or admin."""
    if current_user.role not in ["analyst", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or admin access required"
        )
    return current_user