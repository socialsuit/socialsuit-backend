"""
Authentication API endpoints for API key management and OAuth2.
"""

from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.auth_utils import APIKeyManager, JWTManager, ScopeManager
from app.core.auth_middleware import (
    require_admin, 
    require_auth, 
    AuthContext,
    get_current_auth
)
from app.models.api import ApiKey
from app.api.schemas.auth import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
    OAuth2TokenRequest,
    OAuth2TokenResponse,
    ScopeListResponse,
    ScopeInfo,
    RevokeApiKeyRequest,
    AuthContextResponse,
    ErrorResponse
)


router = APIRouter()
basic_auth = HTTPBasic()


@router.post(
    "/keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API Key",
    description="Create a new API key with specified scopes (admin only)"
)
async def create_api_key(
    key_data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_admin())
):
    """Create a new API key."""
    
    # Generate new API key
    api_key = APIKeyManager.generate_api_key()
    key_hash = APIKeyManager.hash_api_key(api_key)
    
    # Create database record
    db_api_key = ApiKey(
        key_hash=key_hash,
        name=key_data.name,
        description=key_data.description,
        scopes=key_data.scopes,
        created_at=datetime.utcnow()
    )
    
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)
    
    # Return response with the actual key (only shown once)
    return ApiKeyCreateResponse(
        id=db_api_key.id,
        name=db_api_key.name,
        description=db_api_key.description,
        scopes=db_api_key.scopes,
        created_at=db_api_key.created_at,
        last_used_at=db_api_key.last_used_at,
        revoked_at=db_api_key.revoked_at,
        api_key=api_key
    )


@router.get(
    "/keys",
    response_model=ApiKeyListResponse,
    summary="List API Keys",
    description="List all API keys (admin only)"
)
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_admin())
):
    """List all API keys."""
    
    result = await db.execute(select(ApiKey))
    api_keys = result.scalars().all()
    
    return ApiKeyListResponse(
        api_keys=[
            ApiKeyResponse(
                id=key.id,
                name=key.name,
                description=key.description,
                scopes=key.scopes or [],
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                revoked_at=key.revoked_at
            )
            for key in api_keys
        ],
        total=len(api_keys)
    )


@router.get(
    "/keys/{key_id}",
    response_model=ApiKeyResponse,
    summary="Get API Key",
    description="Get details of a specific API key (admin only)"
)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_admin())
):
    """Get details of a specific API key."""
    
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        scopes=api_key.scopes or [],
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        revoked_at=api_key.revoked_at
    )


@router.post(
    "/keys/{key_id}/revoke",
    response_model=ApiKeyResponse,
    summary="Revoke API Key",
    description="Revoke an API key (admin only)"
)
async def revoke_api_key(
    key_id: int,
    revoke_data: RevokeApiKeyRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_admin())
):
    """Revoke an API key."""
    
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already revoked"
        )
    
    # Revoke the key
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == key_id)
        .values(revoked_at=datetime.utcnow())
    )
    await db.commit()
    
    # Refresh to get updated data
    await db.refresh(api_key)
    
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        scopes=api_key.scopes or [],
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        revoked_at=api_key.revoked_at
    )


@router.get(
    "/scopes",
    response_model=ScopeListResponse,
    summary="List Available Scopes",
    description="List all available API scopes"
)
async def list_scopes():
    """List all available API scopes."""
    
    scopes = [
        ScopeInfo(scope=scope, description=description)
        for scope, description in ScopeManager.AVAILABLE_SCOPES.items()
    ]
    
    return ScopeListResponse(scopes=scopes)


@router.get(
    "/me",
    response_model=AuthContextResponse,
    summary="Get Current Auth Context",
    description="Get current authentication context"
)
async def get_current_auth_context(
    auth_context: AuthContext = Depends(require_auth())
):
    """Get current authentication context."""
    
    return AuthContextResponse(
        auth_type=auth_context.auth_type,
        scopes=auth_context.scopes,
        api_key_id=auth_context.api_key_id,
        user_id=auth_context.user_id,
        client_id=auth_context.client_id
    )


# OAuth2 endpoints
oauth_router = APIRouter()


@oauth_router.post(
    "/token",
    response_model=OAuth2TokenResponse,
    summary="OAuth2 Token",
    description="Get access token using client credentials flow"
)
async def get_oauth_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Get access token using OAuth2 client credentials flow."""
    
    # Validate grant type
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant type"
        )
    
    # For this implementation, we'll use API keys as client credentials
    # In a real implementation, you'd have a separate clients table
    
    # Find API key by treating client_id as the API key
    key_hash = APIKeyManager.hash_api_key(client_secret)
    
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
            ApiKey.name == client_id  # Use name as client_id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    # Parse requested scopes
    requested_scopes = scope.split() if scope else []
    
    # Check if requested scopes are available for this API key
    available_scopes = api_key.scopes or []
    
    # Grant intersection of requested and available scopes
    granted_scopes = []
    for requested_scope in requested_scopes:
        if ScopeManager.check_scope_permission(requested_scope, available_scopes):
            granted_scopes.append(requested_scope)
    
    # If no scopes requested, grant all available scopes
    if not requested_scopes:
        granted_scopes = available_scopes
    
    # Create JWT token
    token_data = {
        "client_id": client_id,
        "scopes": granted_scopes,
        "api_key_id": api_key.id
    }
    
    access_token = JWTManager.create_access_token(token_data)
    
    # Update last used timestamp
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key.id)
        .values(last_used_at=datetime.utcnow())
    )
    await db.commit()
    
    return OAuth2TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,  # 1 hour
        scope=" ".join(granted_scopes) if granted_scopes else None
    )