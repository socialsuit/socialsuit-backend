from fastapi import APIRouter, HTTPException
from services.auth.wallet.auth_schema import (
    WalletNonceRequest,
    WalletSignatureVerifyRequest,
    WalletAuthResponse
)
from services.auth.wallet.auth_controller import (
    generate_wallet_nonce,
    verify_wallet_signature_controller
)

router = APIRouter(prefix="/wallet-auth", tags=["Wallet Auth"])

@router.post("/nonce")
async def get_nonce(payload: WalletNonceRequest):
    try:
        return await generate_wallet_nonce(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify", response_model=WalletAuthResponse)
async def verify_signature(payload: WalletSignatureVerifyRequest):
    try:
        return await verify_wallet_signature_controller(payload)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
