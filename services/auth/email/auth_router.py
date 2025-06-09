# services/endpoint/auth_router.py

from fastapi import APIRouter
from services.auth.email.auth_schema import LoginRequest, AuthResponse
from services.auth.email.auth_controller import login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest):
    return login_user(request)
