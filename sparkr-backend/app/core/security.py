import warnings
from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.models.schemas import TokenData

# Import from shared package
from shared.auth.jwt import create_access_token as shared_create_access_token
from shared.auth.jwt import decode_token, get_token_payload
from shared.auth.password import hash_password, verify_password

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    warnings.warn(
        "This function is deprecated. Use shared.auth.password.verify_password instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    warnings.warn(
        "This function is deprecated. Use shared.auth.password.hash_password instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return hash_password(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token"""
    warnings.warn(
        "This function is deprecated. Use shared.auth.jwt.create_access_token instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Convert settings to match shared package expectations
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return shared_create_access_token(
        data=data,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expires_delta=expires_delta
    )


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    """Get the current authenticated user from the token"""
    warnings.warn(
        "This function is deprecated. Consider using shared.auth.jwt functions instead.",
        DeprecationWarning,
        stacklevel=2
    )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Use shared package to decode token
        payload = get_token_payload(token, settings.SECRET_KEY, settings.ALGORITHM)
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(username=email, user_id=user_id)
    except Exception:
        raise credentials_exception
    # Import here to avoid circular imports
    from app.api.v1.auth_router import get_user_by_email
    user = await get_user_by_email(token_data.username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user