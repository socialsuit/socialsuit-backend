# endpoints/callback.py

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse

from services.auth.platform.meta_auth import exchange_code as exchange_meta
from services.auth.platform.linkedin_auth import exchange_code as exchange_linkedin
from services.auth.platform.twitter_auth import exchange_code as exchange_twitter
from services.auth.platform.youtube_auth import exchange_code as exchange_youtube
from services.auth.platform.tiktok_auth import exchange_code as exchange_tiktok
from services.auth.platform.farcaster_auth import handle_farcaster_callback as exchange_farcaster
from services.auth.platform.telegram_auth import handle_telegram_callback as exchange_telegram

router = APIRouter(prefix="/callback", tags=["Platform Callback"])

# ✅ Meta Callback (Facebook/Instagram)
@router.get("/meta")
async def callback_meta(
    code: str = Query(...),
    user_id: str = Query(...)
):
    """
    Meta (FB/IG) redirects here with ?code=&user_id=
    """
    try:
        result = exchange_meta(code, user_id)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ LinkedIn Callback
@router.get("/linkedin")
async def callback_linkedin(
    code: str = Query(...),
    user_id: str = Query(...)
):
    """
    LinkedIn redirects here with ?code=
    """
    try:
        result = exchange_linkedin(code, user_id)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Twitter Callback
@router.get("/twitter")
async def callback_twitter(
    code: str = Query(...),
    user_id: str = Query(...)
):
    """
    Twitter redirects here with ?code=
    """
    try:
        result = exchange_twitter(code, user_id)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# ✅ YouTube Callback
@router.get("/youtube")
async def callback_youtube(
    code: str = Query(...),
    user_id: str = Query(...)
):
    """
    YouTube redirects here with ?code=
    """
    try:
        result = exchange_youtube(code, user_id)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# ✅ TikTok Callback
@router.get("/tiktok")
async def callback_tiktok(
    code: str = Query(...),
    user_id: str = Query(...)
):
    """
    TikTok redirects here with ?code=
    """
    try:
        result = exchange_tiktok(code, user_id)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# ✅ Farcaster Callback
@router.get("/farcaster")
async def callback_farcaster(
    signature: str = Query(...),
    address: str = Query(...),
    nonce: str = Query(...)
):
    try:
        result = exchange_farcaster(signature=signature, address=address, nonce=nonce)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Telegram does not redirect with ?code — uses hash verification
@router.post("/telegram")
async def callback_telegram(
    bot_token: str = Query(...),
    channel_id: str = Query(...)
):
    try:
        result = exchange_telegram(bot_token=bot_token, channel_id=channel_id)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
