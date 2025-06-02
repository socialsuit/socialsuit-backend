# services/auth/auth_schema.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., example="user@example.com", description="Valid email address")
    password: str = Field(..., min_length=8, example="securepassword123", description="Password (min 8 chars)")

class TokenData(BaseModel):
    """Schema for decoded JWT token data."""
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None

class AuthResponse(BaseModel):
    """Schema for authentication response."""
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", example="bearer")
    expires_in: Optional[int] = Field(default=3600, example=3600, description="Token expiry in seconds")
    refresh_token: Optional[str] = Field(None, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

class UserInDB(BaseModel):
    """Schema for user data in database."""
    id: str
    email: EmailStr
    hashed_password: str
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

