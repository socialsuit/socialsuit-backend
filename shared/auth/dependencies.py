"""Shared authentication dependencies for FastAPI."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from services.database.database import get_db
from services.auth.unified_auth_service import auth_service
from services.models.user_model import User

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from JWT token (required)."""
    token = credentials.credentials
    payload = auth_service.verify_token(token, "access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db: Session = Depends(get_db)) -> Optional[User]:
    """Get current authenticated user from JWT token (optional)."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = auth_service.verify_token(token, "access")
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None


def require_email_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require user to have email authentication set up."""
    if not current_user.has_email_auth():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email authentication required for this action"
        )
    return current_user


def require_wallet_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require user to have wallet authentication set up."""
    if not current_user.has_wallet_auth():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wallet authentication required for this action"
        )
    return current_user


def require_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Require user to be verified (either email or wallet)."""
    if not (current_user.email_verified or current_user.wallet_verified):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account verification required for this action"
        )
    return current_user


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require user to have admin privileges."""
    # Add admin check logic here based on your requirements
    # For now, this is a placeholder
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action"
        )
    return current_user