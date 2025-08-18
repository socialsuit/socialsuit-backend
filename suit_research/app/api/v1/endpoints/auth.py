"""Unified authentication endpoints for Suit Research."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.auth_schemas import (
    UserCreateEmail,
    UserCreateWallet,
    UserLoginEmail,
    UserLoginWallet,
    WalletChallenge,
    WalletChallengeResponse,
    LinkEmailRequest,
    LinkWalletRequest,
    UnlinkWalletRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfile,
    AuthMethodsResponse,
    ChangePasswordRequest,
    MessageResponse,
    ErrorResponse
)

# Import shared auth service
try:
    from app.shared.auth.unified_auth_service import UnifiedAuthService
    from app.shared.auth.dependencies import get_current_user, get_current_user_optional
except ImportError:
    # Fallback for local development
    from app.services.auth.unified_auth_service import UnifiedAuthService
    from app.services.auth.dependencies import get_current_user, get_current_user_optional


# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
router.state.limiter = limiter
router.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

security = HTTPBearer()
auth_service = UnifiedAuthService()


@router.post("/register/email", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register_with_email(
    request: Request,
    user_data: UserCreateEmail,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Register a new user with email and password."""
    try:
        user = await auth_service.register_user_email(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            db=db
        )
        
        # Generate tokens
        access_token = auth_service.create_access_token(data={"sub": str(user.id)})
        refresh_token = auth_service.create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/register/wallet", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register_with_wallet(
    request: Request,
    user_data: UserCreateWallet,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Register a new user with wallet."""
    try:
        # Verify wallet signature
        is_valid = auth_service.verify_wallet_signature(
            wallet_address=user_data.wallet_address,
            message=user_data.message,
            signature=user_data.signature
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid wallet signature"
            )
        
        user = await auth_service.register_user_wallet(
            wallet_address=user_data.wallet_address,
            network=user_data.network,
            full_name=user_data.full_name,
            db=db
        )
        
        # Generate tokens
        access_token = auth_service.create_access_token(data={"sub": str(user.id)})
        refresh_token = auth_service.create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login/email", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_with_email(
    request: Request,
    login_data: UserLoginEmail,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Login with email and password."""
    try:
        user = await auth_service.authenticate_user_email(
            email=login_data.email,
            password=login_data.password,
            db=db
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token = auth_service.create_access_token(data={"sub": str(user.id)})
        refresh_token = auth_service.create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/login/wallet", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_with_wallet(
    request: Request,
    login_data: UserLoginWallet,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Login with wallet signature."""
    try:
        # Verify wallet signature
        is_valid = auth_service.verify_wallet_signature(
            wallet_address=login_data.wallet_address,
            message=login_data.message,
            signature=login_data.signature
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid wallet signature"
            )
        
        user = await auth_service.authenticate_user_wallet(
            wallet_address=login_data.wallet_address,
            network=login_data.network,
            db=db
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wallet not registered"
            )
        
        # Generate tokens
        access_token = auth_service.create_access_token(data={"sub": str(user.id)})
        refresh_token = auth_service.create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/wallet/challenge", response_model=WalletChallengeResponse)
@limiter.limit("20/minute")
async def get_wallet_challenge(
    request: Request,
    challenge_data: WalletChallenge
) -> WalletChallengeResponse:
    """Generate a challenge message for wallet authentication."""
    challenge = auth_service.generate_wallet_challenge(
        wallet_address=challenge_data.wallet_address,
        network=challenge_data.network
    )
    return challenge


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    try:
        tokens = await auth_service.refresh_access_token(
            refresh_token=token_data.refresh_token,
            db=db
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/link/email", response_model=MessageResponse)
@limiter.limit("5/minute")
async def link_email_to_account(
    request: Request,
    link_data: LinkEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Link email/password authentication to existing wallet account."""
    try:
        await auth_service.link_email_to_user(
            user_id=current_user.id,
            email=link_data.email,
            password=link_data.password,
            db=db
        )
        return MessageResponse(message="Email successfully linked to account")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/link/wallet", response_model=MessageResponse)
@limiter.limit("5/minute")
async def link_wallet_to_account(
    request: Request,
    link_data: LinkWalletRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Link wallet authentication to existing email account."""
    try:
        # Verify wallet signature
        is_valid = auth_service.verify_wallet_signature(
            wallet_address=link_data.wallet_address,
            message=link_data.message,
            signature=link_data.signature
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid wallet signature"
            )
        
        await auth_service.link_wallet_to_user(
            user_id=current_user.id,
            wallet_address=link_data.wallet_address,
            network=link_data.network,
            db=db
        )
        return MessageResponse(message="Wallet successfully linked to account")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/unlink/wallet", response_model=MessageResponse)
@limiter.limit("5/minute")
async def unlink_wallet_from_account(
    request: Request,
    unlink_data: UnlinkWalletRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Unlink wallet from account."""
    try:
        await auth_service.unlink_wallet_from_user(
            user_id=current_user.id,
            wallet_address=unlink_data.wallet_address,
            db=db
        )
        return MessageResponse(message="Wallet successfully unlinked from account")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """Get current user's profile with authentication methods."""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        wallet_address=current_user.wallet_address,
        network=current_user.network,
        auth_type=current_user.auth_type,
        role=current_user.role,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        email_verified=current_user.email_verified,
        wallet_verified=current_user.wallet_verified,
        auth_methods=current_user.get_auth_methods(),
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get("/auth-methods", response_model=AuthMethodsResponse)
async def get_auth_methods(
    current_user: User = Depends(get_current_user)
) -> AuthMethodsResponse:
    """Get user's available authentication methods."""
    return AuthMethodsResponse(
        user_id=str(current_user.id),
        auth_methods=current_user.get_auth_methods(),
        auth_type=current_user.auth_type,
        email_verified=current_user.email_verified,
        wallet_verified=current_user.wallet_verified
    )


@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Change user's password."""
    try:
        # Verify current password
        if not current_user.has_email_auth():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email authentication not set up"
            )
        
        if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.hashed_password = auth_service.hash_password(password_data.new_password)
        db.commit()
        
        return MessageResponse(message="Password successfully changed")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """Logout user (client should discard tokens)."""
    # In a production environment, you might want to blacklist the token
    # For now, we'll just return a success message
    return MessageResponse(message="Successfully logged out")