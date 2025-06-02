from fastapi import APIRouter, Depends
from services.auth.auth_guard import auth_required
from models.user import User

router = APIRouter(prefix="/secure", tags=["Protected"])

@router.get("/me")
def get_profile(current_user: User = Depends(auth_required)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "wallet": current_user.wallet_address,
        "network": current_user.network,
        "verified": current_user.is_verified
    }
