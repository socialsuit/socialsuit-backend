"""Authentication schemas for unified auth system."""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from enum import Enum


class AuthType(str, Enum):
    EMAIL = "email"
    WALLET = "wallet"
    HYBRID = "hybrid"


# User Creation Schemas
class UserCreateEmail(BaseModel):
    """Schema for creating user with email/password."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserCreateWallet(BaseModel):
    """Schema for creating user with wallet."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    network: str = Field(default="ethereum")
    signature: str
    message: str
    full_name: Optional[str] = None
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError('Wallet address must start with 0x')
        if len(v) != 42:
            raise ValueError('Wallet address must be 42 characters long')
        return v.lower()


# Login Schemas
class UserLoginEmail(BaseModel):
    """Schema for email/password login."""
    email: EmailStr
    password: str


class UserLoginWallet(BaseModel):
    """Schema for wallet login."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    network: str = Field(default="ethereum")
    signature: str
    message: str
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError('Wallet address must start with 0x')
        if len(v) != 42:
            raise ValueError('Wallet address must be 42 characters long')
        return v.lower()


# Wallet Challenge Schema
class WalletChallenge(BaseModel):
    """Schema for wallet challenge generation."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    network: str = Field(default="ethereum")
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError('Wallet address must start with 0x')
        if len(v) != 42:
            raise ValueError('Wallet address must be 42 characters long')
        return v.lower()


class WalletChallengeResponse(BaseModel):
    """Schema for wallet challenge response."""
    message: str
    expires_at: datetime


# Account Linking Schemas
class LinkEmailRequest(BaseModel):
    """Schema for linking email to existing wallet account."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class LinkWalletRequest(BaseModel):
    """Schema for linking wallet to existing email account."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    network: str = Field(default="ethereum")
    signature: str
    message: str
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError('Wallet address must start with 0x')
        if len(v) != 42:
            raise ValueError('Wallet address must be 42 characters long')
        return v.lower()


class UnlinkWalletRequest(BaseModel):
    """Schema for unlinking wallet from account."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError('Wallet address must start with 0x')
        if len(v) != 42:
            raise ValueError('Wallet address must be 42 characters long')
        return v.lower()


# Token Schemas
class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


# User Profile Schemas
class UserProfile(BaseModel):
    """Schema for user profile response."""
    id: str
    email: Optional[str] = None
    wallet_address: Optional[str] = None
    network: Optional[str] = None
    auth_type: AuthType
    role: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    email_verified: bool
    wallet_verified: bool
    auth_methods: List[str]
    created_at: datetime
    last_login: datetime
    
    class Config:
        from_attributes = True


class AuthMethodsResponse(BaseModel):
    """Schema for authentication methods response."""
    user_id: str
    auth_methods: List[str]
    auth_type: AuthType
    email_verified: bool
    wallet_verified: bool


# Password Management Schemas
class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Response Schemas
class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    success: bool = False