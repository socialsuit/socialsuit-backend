"""
Authentication utilities for API keys and JWT tokens.
"""

import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


class APIKeyManager:
    """Manages API key generation, hashing, and verification."""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key."""
        return f"sk_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return hmac.compare_digest(
            hashlib.sha256(api_key.encode()).hexdigest(),
            hashed_key
        )


class JWTManager:
    """Manages JWT token creation and verification."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )


class ScopeManager:
    """Manages API scopes and permissions."""
    
    # Available scopes
    AVAILABLE_SCOPES = {
        "read:public": "Read public project information",
        "read:funding": "Read funding round data",
        "read:investors": "Read investor information",
        "write:webhooks": "Create and manage webhooks",
        "admin": "Full administrative access"
    }
    
    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> bool:
        """Validate that all provided scopes are valid."""
        return all(scope in cls.AVAILABLE_SCOPES for scope in scopes)
    
    @classmethod
    def check_scope_permission(cls, required_scope: str, user_scopes: List[str]) -> bool:
        """Check if user has required scope permission."""
        # Admin scope grants all permissions
        if "admin" in user_scopes:
            return True
        
        return required_scope in user_scopes
    
    @classmethod
    def get_scope_description(cls, scope: str) -> str:
        """Get description for a scope."""
        return cls.AVAILABLE_SCOPES.get(scope, "Unknown scope")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)