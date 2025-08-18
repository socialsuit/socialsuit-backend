"""Authentication middleware for unified auth across platforms."""

from typing import Optional, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from .unified_auth_service import auth_service


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication across both platforms."""
    
    def __init__(self, app, db_session_factory: Callable[[], Session]):
        super().__init__(app)
        self.db_session_factory = db_session_factory
        
        # Paths that don't require authentication
        self.public_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/register/email",
            "/auth/register/wallet",
            "/auth/login/email",
            "/auth/login/wallet",
            "/auth/wallet/challenge",
            "/auth/refresh"
        }
        
        # Paths that require authentication
        self.protected_paths = {
            "/auth/profile",
            "/auth/methods",
            "/auth/link/",
            "/auth/unlink/",
            "/auth/change-password",
            "/auth/logout"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add user context if authenticated."""
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        
        user = None
        if scheme and scheme.lower() == "bearer" and token:
            # Get database session
            db = self.db_session_factory()
            try:
                user = auth_service.get_user_from_token(db, token)
            except Exception:
                pass
            finally:
                db.close()
        
        # Add user to request state
        request.state.user = user
        
        # Check if protected path requires authentication
        if self._is_protected_path(request.url.path) and not user:
            return Response(
                content='{"detail": "Authentication required"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        response = await call_next(request)
        return response
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require authentication)."""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path is protected (requires authentication)."""
        return any(path.startswith(protected_path) for protected_path in self.protected_paths)


def get_user_from_request(request: Request):
    """Get user from request state (set by middleware)."""
    return getattr(request.state, 'user', None)


def require_auth_from_request(request: Request):
    """Require authentication from request state."""
    user = get_user_from_request(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user