# services/auth/farcaster_auth.py

# Farcaster is mostly crypto-wallet-based (Sign-in with Ethereum).
# Example for handling an auth signature:

from fastapi import Request
from services.database.database import get_db
from services.models.token_model import PlatformToken

def get_farcaster_login_url() -> str:
    # For frontends, you may show a wallet connect modal
    return "Wallet connect flow handled on frontend"


def handle_farcaster_callback(request: Request):
    signature = request.query_params.get("signature")
    user_address = request.query_params.get("address")

    if not signature or not user_address:
        return {"error": "Missing Farcaster signature or address"}

    db = next(get_db())
    new_token = PlatformToken(
        user_id="PLACEHOLDER",
        platform="farcaster",
        access_token=signature  # Store signature as token
    )
    db.add(new_token)
    db.commit()

    return {"msg": "Farcaster connected!", "address": user_address}
