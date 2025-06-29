# endpoints/callback.py

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse

from services.auth.platform.meta_auth import exchange_code as exchange_meta
from services.auth.platform.linkedin_auth import exchange_code as exchange_linkedin
from services.auth.platform.twitter_auth import exchange_code as exchange_twitter
from services.auth.platform.youtube_auth import exchange_code as exchange_youtube
from services.auth.platform.tiktok_auth import exchange_code as exchange_tiktok
from services.auth.platform.farcaster_auth import exchange_code as exchange_farcaster
from services.auth.platform.telegram_auth import verify_telegram

router = APIRouter(prefix="/callback", tags=["Platform Callback"])

# ✅ Meta Callback (Facebook/Instagram)
@router.get("/meta")
async def callback_meta(code: str = Query(...)):
    """
    Meta (FB/IG) redirects here with ?code=
    """
    try:
        result = exchange_meta(code)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ LinkedIn Callback
@router.get("/linkedin")
async def callback_linkedin(code: str = Query(...)):
    """
    LinkedIn OAuth callback.
    """
    try:
        result = exchange_linkedin(code)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Twitter Callback
@router.get("/twitter")
async def callback_twitter(code: str = Query(...)):
    """
    Twitter OAuth callback.
    """
    try:
        result = exchange_twitter(code)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ YouTube Callback
@router.get("/youtube")
async def callback_youtube(code: str = Query(...)):
    """
    YouTube OAuth callback.
    """
    try:
        result = exchange_youtube(code)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ TikTok Callback
@router.get("/tiktok")
async def callback_tiktok(code: str = Query(...)):
    """
    TikTok OAuth callback.
    """
    try:
        result = exchange_tiktok(code)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Farcaster Callback
@router.get("/farcaster")
async def callback_farcaster(code: str = Query(...)):
    """
    Farcaster auth callback.
    """
    try:
        result = exchange_farcaster(code)
        return JSONResponse(content={"success": True, "details": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Telegram does not redirect with ?code — uses hash verification
@router.post("/telegram")
async def callback_telegram(request: Request):
    """
    Telegram Login Widget posts data — verify hash here.
    """
    data = await request.json()
    try:
        verified = verify_telegram(data)
        return JSONResponse(content={"success": True, "details": verified})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

