import jwt
from datetime import datetime, timedelta
from core.config import settings

def create_jwt_token(user_id: str, email: str = None, wallet_address: str = None):
    payload = {
        "sub": user_id,
        "email": email,
        "wallet_address": wallet_address,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return {
        "access_token": jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256"),
        "refresh_token": None,
        "token_type": "bearer",
        "expires_in": 3600
    }
