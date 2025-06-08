from datetime import datetime, timedelta
from jose import jwt
import secrets

from services.models.user_model import User as WalletUserModel  # Assuming you're using a DB model
from auth.wallet.auth_schema import (
    WalletNonceRequest,
    WalletSignatureVerifyRequest,
    WalletAuthResponse,
    WalletNetwork,
)
from auth.jwt_handler import create_access_token, create_refresh_token
from auth.wallet.auth_schema import verify_wallet_signature  # Custom EVM signature checker
from services.database.database import db  # Your DB session

# In-memory nonce store (replace with Redis or DB in production)
NONCE_STORE = {}

async def generate_wallet_nonce(payload: WalletNonceRequest):
    nonce = secrets.token_hex(16)
    key = f"{payload.network}:{payload.address}"
    NONCE_STORE[key] = nonce

    return {"nonce": nonce}

async def verify_wallet_signature_controller(payload: WalletSignatureVerifyRequest):
    key = f"{payload.network}:{payload.address}"
    expected_nonce = NONCE_STORE.get(key)

    if not expected_nonce or payload.nonce != expected_nonce:
        raise ValueError("Invalid or expired nonce")

    # Signature Verification
    is_valid = verify_wallet_signature(
        address=payload.address,
        signature=payload.signature,
        message=expected_nonce,
        network=payload.network
    )
    if not is_valid:
        raise ValueError("Signature verification failed")

    # Save or update user in DB
    user = await db.get_wallet_user(payload.address, payload.network)
    now = datetime.utcnow()
    if not user:
        user = WalletUserModel(
            wallet_address=payload.address,
            network=payload.network,
            first_auth_date=now,
            last_login=now,
            is_verified=True
        )
        await db.save_wallet_user(user)
    else:
        user.last_login = now
        await db.update_wallet_user(user)

    # Token generation
    access_token = create_access_token(data={"wallet": payload.address})
    refresh_token = create_refresh_token(data={"wallet": payload.address})

    return WalletAuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
        wallet_address=payload.address
    )
