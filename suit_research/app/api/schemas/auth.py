"""
Authentication schemas for API requests and responses.
"""

from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator


class ApiKeyCreate(BaseModel):
    """Schema for creating an API key."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Name for the API key")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    scopes: List[str] = Field(..., description="List of scopes/permissions")
    
    @validator('scopes')
    def validate_scopes(cls, v):
        from app.core.auth_utils import ScopeManager
        if not ScopeManager.validate_scopes(v):
            raise ValueError("Invalid scopes provided")
        return v


class ApiKeyResponse(BaseModel):
    """Schema for API key response."""
    
    id: int
    name: str
    description: Optional[str]
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    revoked_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyResponse):
    """Schema for API key creation response (includes the actual key)."""
    
    api_key: str = Field(..., description="The actual API key (only shown once)")


class OAuth2TokenRequest(BaseModel):
    """Schema for OAuth2 client credentials token request."""
    
    grant_type: str = Field(..., description="Must be 'client_credentials'")
    client_id: str = Field(..., description="Client ID")
    client_secret: str = Field(..., description="Client secret")
    scope: Optional[str] = Field(None, description="Space-separated list of scopes")
    
    @validator('grant_type')
    def validate_grant_type(cls, v):
        if v != 'client_credentials':
            raise ValueError("Only 'client_credentials' grant type is supported")
        return v


class OAuth2TokenResponse(BaseModel):
    """Schema for OAuth2 token response."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None


class ScopeInfo(BaseModel):
    """Schema for scope information."""
    
    scope: str
    description: str


class ScopeListResponse(BaseModel):
    """Schema for listing available scopes."""
    
    scopes: List[ScopeInfo]


class ApiKeyListResponse(BaseModel):
    """Schema for listing API keys."""
    
    api_keys: List[ApiKeyResponse]
    total: int


class RevokeApiKeyRequest(BaseModel):
    """Schema for revoking an API key."""
    
    revoke: bool = True


class AuthContextResponse(BaseModel):
    """Schema for current authentication context."""
    
    auth_type: str
    scopes: List[str]
    api_key_id: Optional[int] = None
    user_id: Optional[int] = None
    client_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    error: str
    error_description: Optional[str] = None