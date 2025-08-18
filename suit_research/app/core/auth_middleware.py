"""
Authentication middleware for API key and JWT token validation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.auth_utils import APIKeyManager, JWTManager, ScopeManager
from app.core.redis_client import get_redis_client
from app.models.api import ApiKey
import redis.asyncio as redis


security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RateLimitError(HTTPException):
    """Custom rate limit error."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "60"}
        )


class AuthContext:
    """Authentication context containing user/API key info."""
    
    def __init__(
        self,
        auth_type: str,  # "api_key" or "jwt"
        scopes: List[str],
        api_key_id: Optional[int] = None,
        user_id: Optional[int] = None,
        client_id: Optional[str] = None
    ):
        self.auth_type = auth_type
        self.scopes = scopes
        self.api_key_id = api_key_id
        self.user_id = user_id
        self.client_id = client_id


class RateLimiter:
    """Redis-based rate limiter for API keys."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int = 1000,  # requests per hour
        window: int = 3600  # 1 hour in seconds
    ) -> bool:
        """Check if request is within rate limit."""
        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - window
        
        # Use sliding window rate limiting
        pipe = self.redis.pipeline()
        
        # Remove old entries
        await pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_count = await pipe.zcard(key)
        
        if current_count >= limit:
            return False
        
        # Add current request
        await pipe.zadd(key, {str(current_time): current_time})
        await pipe.expire(key, window)
        await pipe.execute()
        
        return True


async def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    redis_client = await get_redis_client()
    return RateLimiter(redis_client)


async def authenticate_api_key(
    api_key: str,
    db: AsyncSession,
    rate_limiter: RateLimiter
) -> AuthContext:
    """Authenticate using API key."""
    
    # Hash the provided key
    key_hash = APIKeyManager.hash_api_key(api_key)
    
    # Find API key in database
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None)
        )
    )
    api_key_obj = result.scalar_one_or_none()
    
    if not api_key_obj:
        raise AuthenticationError("Invalid API key")
    
    # Check rate limit
    rate_limit_key = f"rate_limit:api_key:{api_key_obj.id}"
    if not await rate_limiter.check_rate_limit(rate_limit_key):
        raise RateLimitError("API key rate limit exceeded")
    
    # Update last used timestamp
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key_obj.id)
        .values(last_used_at=datetime.utcnow())
    )
    await db.commit()
    
    return AuthContext(
        auth_type="api_key",
        scopes=api_key_obj.scopes or [],
        api_key_id=api_key_obj.id
    )


async def authenticate_jwt(token: str) -> AuthContext:
    """Authenticate using JWT token."""
    
    payload = JWTManager.verify_token(token)
    
    return AuthContext(
        auth_type="jwt",
        scopes=payload.get("scopes", []),
        user_id=payload.get("user_id"),
        client_id=payload.get("client_id")
    )


async def get_current_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
) -> Optional[AuthContext]:
    """Get current authentication context."""
    
    if not credentials:
        return None
    
    auth_header = credentials.credentials
    scheme = credentials.scheme.lower()
    
    if scheme == "bearer":
        # JWT token authentication
        return await authenticate_jwt(auth_header)
    
    elif scheme == "apikey":
        # API key authentication
        return await authenticate_api_key(auth_header, db, rate_limiter)
    
    else:
        # Check if it's an API key with custom scheme
        if auth_header.startswith("ApiKey "):
            api_key = auth_header[7:]  # Remove "ApiKey " prefix
            return await authenticate_api_key(api_key, db, rate_limiter)
    
    raise AuthenticationError("Invalid authentication scheme")


def require_auth(required_scopes: List[str] = None):
    """Dependency to require authentication with optional scope checking."""
    
    async def _require_auth(
        auth_context: Optional[AuthContext] = Depends(get_current_auth)
    ) -> AuthContext:
        
        if not auth_context:
            raise AuthenticationError("Authentication required")
        
        # Check required scopes
        if required_scopes:
            for scope in required_scopes:
                if not ScopeManager.check_scope_permission(scope, auth_context.scopes):
                    raise AuthorizationError(
                        f"Missing required scope: {scope}"
                    )
        
        return auth_context
    
    return _require_auth


def require_scope(scope: str):
    """Dependency to require a specific scope."""
    return require_auth([scope])


def require_admin():
    """Dependency to require admin access."""
    return require_scope("admin")


async def get_current_user(
    auth_context: AuthContext = Depends(require_auth())
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user.
    
    Returns user information from the authentication context.
    This is a simplified implementation that returns user data as a dict.
    """
    return {
        "id": auth_context.user_id or 1,  # Default to 1 if no user_id
        "type": auth_context.auth_type,
        "scopes": auth_context.scopes
    }


async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
) -> str:
    """
    Dependency to extract and validate API key from request.
    
    Returns the raw API key string after validation.
    Used for endpoints that need the actual API key value.
    """
    if not credentials:
        raise AuthenticationError("API key required")
    
    auth_header = credentials.credentials
    scheme = credentials.scheme.lower()
    
    api_key = None
    
    if scheme == "apikey":
        api_key = auth_header
    elif auth_header.startswith("ApiKey "):
        api_key = auth_header[7:]  # Remove "ApiKey " prefix
    else:
        raise AuthenticationError("Invalid API key format. Use 'ApiKey your_key_here'")
    
    # Validate the API key
    auth_context = await authenticate_api_key(api_key, db, rate_limiter)
    
    if not auth_context:
        raise AuthenticationError("Invalid API key")
    
    return api_key