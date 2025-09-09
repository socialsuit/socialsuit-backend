from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from sparkr.app.core.config import settings
from sparkr.app.core.security import get_password_hash, create_access_token
from sparkr.app.db.session import get_session
from sparkr.app.models.schemas import UserCreate, UserResponse, Token, TokenData
from sparkr.app.models.models import User
from sparkr.app.services.user_service import get_user_by_email, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Register a new user"""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email, session)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    # Add to database
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        created_at=new_user.created_at,
        is_active=new_user.is_active,
        total_points=0
    )


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    """Get access token for authenticated user"""
    # OAuth2PasswordRequestForm uses username field, but we're treating it as email
    user = await authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    """Get current authenticated user"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=email, user_id=payload.get("user_id"))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_email(token_data.username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        is_active=user.is_active,
        total_points=0  # This would be fetched from a points service in a real app
    )