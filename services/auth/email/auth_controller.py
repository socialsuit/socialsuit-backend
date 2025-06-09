# services/auth/controller.py

from datetime import timedelta, datetime
from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from services.auth.email.auth_schema import LoginRequest, AuthResponse, UserInDB
from typing import Optional

# Secret config values (ideally from environment or settings.py)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dummy user DB (replace with real DB query)
fake_user_db = {
    "user@example.com": UserInDB(
        id="123",
        email="user@example.com",
        hashed_password=pwd_context.hash("securepassword123"),
        disabled=False
    )
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = fake_user_db.get(email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def login_user(request: LoginRequest) -> AuthResponse:
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return AuthResponse(access_token=access_token, token_type="bearer", expires_in=3600)
