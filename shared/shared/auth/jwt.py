"""JWT authentication utilities.

This module provides functions for creating, decoding, and validating JWT tokens.
It also includes FastAPI dependencies for token validation and scope checking.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError


class TokenPayload(BaseModel):
    """Model for JWT token payload."""
    sub: str  # Subject (typically user ID or email)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at time
    scope: str = "access"  # Token scope (access, refresh, etc.)
    jti: Optional[str] = None  # JWT ID (unique identifier for the token)
    iss: Optional[str] = None  # Issuer
    aud: Optional[str] = None  # Audience
    nbf: Optional[datetime] = None  # Not valid before time
    scopes: List[str] = []  # List of permission scopes
    additional_claims: Optional[Dict[str, Any]] = None  # Any additional custom claims


class TokenValidationError(BaseModel):
    """Model for token validation errors."""
    code: str
    detail: str


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "admin": "Full access to all resources",
        "user": "Standard user access",
        "refresh": "Refresh token access"
    }
)


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    secret_key: str = "your-secret-key",  # Should be loaded from config
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
) -> TokenPayload:
    """FastAPI dependency to validate JWT token and return current user.
    
    Args:
        security_scopes: The security scopes required for the endpoint
        token: The JWT token from the Authorization header
        secret_key: The secret key used to verify the token
        audience: Optional expected audience
        issuer: Optional expected issuer
        
    Returns:
        The TokenPayload with validated user data
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't have required scopes
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    result = validate_token(
        token=token,
        secret_key=secret_key,
        required_scopes=security_scopes.scopes,
        audience=audience,
        issuer=issuer
    )
    
    if isinstance(result, TokenValidationError):
        if result.code == "insufficient_scope":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result.detail,
                headers={"WWW-Authenticate": authenticate_value},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.detail,
                headers={"WWW-Authenticate": authenticate_value},
            )
    
    return result


def get_auth_dependency(
    required_scopes: List[str] = None,
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
    secret_key: Optional[str] = None,
) -> Callable:
    """Create a dependency for route protection with specific scopes.
    
    This is a factory function that creates a FastAPI dependency with predefined
    scopes and settings. It's useful for creating reusable auth guards.
    
    Args:
        required_scopes: List of required scopes for the protected route
        audience: Expected audience for token validation
        issuer: Expected issuer for token validation
        secret_key: Secret key for token validation (defaults to config value)
        
    Returns:
        A FastAPI dependency function that can be used with Depends()
        
    Example:
        ```python
        # Create auth guards with different permission requirements
        require_admin = get_auth_dependency(["admin"])
        require_user = get_auth_dependency(["user"])
        
        @app.get("/admin-only", dependencies=[Depends(require_admin)])
        def admin_route():
            return {"message": "Admin access granted"}
        ```
    """
    security_scopes = SecurityScopes(scopes=required_scopes or [])
    
    async def auth_dependency(
        token: str = Depends(oauth2_scheme),
    ) -> TokenPayload:
        nonlocal secret_key
        if secret_key is None:
            # In a real implementation, this would load from config
            secret_key = "your-secret-key"
            
        return await get_current_user(
            security_scopes=security_scopes,
            token=token,
            secret_key=secret_key,
            audience=audience,
            issuer=issuer,
        )
        
    return auth_dependency


# Pre-configured auth guards for common use cases
require_admin = get_auth_dependency(["admin"])
require_user = get_auth_dependency(["user"])
require_refresh_token = get_auth_dependency(["refresh"])


def create_access_token(
    subject: Union[str, int],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
    scopes: List[str] = None,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    """Create a new JWT access token.
    
    Args:
        subject: The subject of the token, typically a user ID or email
        secret_key: The secret key used to sign the token
        algorithm: The algorithm used to sign the token
        expires_delta: Optional expiration time delta
        additional_claims: Optional additional claims to include in the token
        scopes: Optional list of permission scopes
        issuer: Optional issuer claim
        audience: Optional audience claim
        
    Returns:
        A JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=15)
        
    now = datetime.utcnow()
    expire = now + expires_delta
    
    # Create a unique token ID
    import uuid
    token_id = str(uuid.uuid4())
    
    to_encode = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "jti": token_id,
        "scope": "access",
    }
    
    # Add optional claims
    if scopes:
        to_encode["scopes"] = scopes
    if issuer:
        to_encode["iss"] = issuer
    if audience:
        to_encode["aud"] = audience
    if additional_claims:
        to_encode.update(additional_claims)
        
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_refresh_token(
    subject: Union[str, int],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    """Create a new JWT refresh token.
    
    Args:
        subject: The subject of the token, typically a user ID or email
        secret_key: The secret key used to sign the token
        algorithm: The algorithm used to sign the token
        expires_delta: Optional expiration time delta (longer than access token)
        additional_claims: Optional additional claims to include in the token
        issuer: Optional issuer claim
        audience: Optional audience claim
        
    Returns:
        A JWT refresh token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)  # Refresh tokens typically last longer
    
    # Use the same function but with different scope and expiration
    refresh_claims = additional_claims.copy() if additional_claims else {}
    
    # Create a unique token ID
    import uuid
    token_id = str(uuid.uuid4())
    
    # Add refresh-specific claims
    refresh_claims.update({"jti": token_id})
    
    return create_access_token(
        subject=subject,
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=expires_delta,
        additional_claims=refresh_claims,
        scopes=["refresh"],
        issuer=issuer,
        audience=audience
    )


def decode_token(
    token: str,
    secret_key: str,
    algorithms: list[str] = ["HS256"],
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
) -> Dict[str, Any]:
    """Decode a JWT token.
    
    Args:
        token: The JWT token to decode
        secret_key: The secret key used to verify the token
        algorithms: The algorithms that can be used to verify the token
        audience: Optional expected audience
        issuer: Optional expected issuer
        
    Returns:
        The decoded token payload
        
    Raises:
        JWTError: If the token is invalid or expired
    """
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_aud": audience is not None,
        "verify_iss": issuer is not None,
    }
    
    return jwt.decode(
        token, 
        secret_key, 
        algorithms=algorithms,
        audience=audience,
        issuer=issuer,
        options=options
    )


def get_token_payload(
    token: str, 
    secret_key: str,
    algorithms: list[str] = ["HS256"],
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
) -> TokenPayload:
    """Get the payload from a JWT token as a Pydantic model.
    
    Args:
        token: The JWT token
        secret_key: The secret key used to verify the token
        algorithms: The algorithms that can be used to verify the token
        audience: Optional expected audience
        issuer: Optional expected issuer
        
    Returns:
        A TokenPayload instance with the token claims
        
    Raises:
        JWTError: If the token is invalid or expired
        ValidationError: If the token payload doesn't match the expected schema
    """
    payload = decode_token(
        token, 
        secret_key, 
        algorithms=algorithms,
        audience=audience,
        issuer=issuer
    )
    return TokenPayload(**payload)


def validate_token(
    token: str,
    secret_key: str,
    required_scopes: List[str] = None,
    algorithms: list[str] = ["HS256"],
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
) -> Union[TokenPayload, TokenValidationError]:
    """Validate a JWT token and check required scopes.
    
    Args:
        token: The JWT token to validate
        secret_key: The secret key used to verify the token
        required_scopes: Optional list of required scopes
        algorithms: The algorithms that can be used to verify the token
        audience: Optional expected audience
        issuer: Optional expected issuer
        
    Returns:
        Either a valid TokenPayload or a TokenValidationError
    """
    try:
        payload = get_token_payload(
            token, 
            secret_key, 
            algorithms=algorithms,
            audience=audience,
            issuer=issuer
        )
        
        # Check if token has required scopes
        if required_scopes:
            token_scopes = set(payload.scopes)
            if not any(scope in token_scopes for scope in required_scopes):
                return TokenValidationError(
                    code="insufficient_scope",
                    detail=f"Token doesn't have the required scopes: {', '.join(required_scopes)}"
                )
        
        return payload
    except JWTError as e:
        return TokenValidationError(
            code="invalid_token",
            detail=f"Invalid token: {str(e)}"
        )
    except ValidationError as e:
        return TokenValidationError(
            code="invalid_claims",
            detail=f"Invalid token claims: {str(e)}"
        )
    except Exception as e:
        return TokenValidationError(
            code="token_validation_error",
            detail=f"Token validation error: {str(e)}"
        )