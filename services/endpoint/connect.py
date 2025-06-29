# services/endpoints/connect.py

from fastapi import APIRouter, Request
from services.auth.platform.meta_auth import get_meta_login_url, handle_meta_callback
from services.auth.platform.twitter_auth import get_twitter_login_url, handle_twitter_callback
from services.auth.platform.linkedin_auth import get_linkedin_login_url, handle_linkedin_callback
from services.auth.platform.farcaster_auth import get_farcaster_login_url, handle_farcaster_callback
from services.auth.platform.tiktok_auth import get_tiktok_login_url, handle_tiktok_callback
from services.auth.platform.youtube_auth import get_youtube_login_url, handle_youtube_callback
from services.auth.platform.telegram_auth import get_telegram_connect_instructions, handle_telegram_callback

router = APIRouter()

@router.get("/connect/meta")
def connect_meta():
    return {"auth_url": get_meta_login_url()}

@router.get("/callback/meta")
def callback_meta(request: Request):
    return handle_meta_callback(request)

@router.get("/connect/twitter")
def connect_twitter():
    return {"auth_url": get_twitter_login_url()}

@router.get("/callback/twitter")
def callback_twitter(request: Request):
    return handle_twitter_callback(request)

@router.get("/connect/linkedin")
def connect_linkedin():
    return {"auth_url": get_linkedin_login_url()}

@router.get("/callback/linkedin")
def callback_linkedin(request: Request):
    return handle_linkedin_callback(request)

@router.get("/connect/farcaster")
def connect_farcaster():
    return {"auth_url": get_farcaster_login_url()}

@router.get("/callback/farcaster")
def callback_farcaster(request: Request):
    return handle_farcaster_callback(request)

@router.get("/connect/tiktok")
def connect_tiktok():
    return {"auth_url": get_tiktok_login_url()}

@router.get("/callback/tiktok")
def callback_tiktok(request: Request):
    return handle_tiktok_callback(request)

@router.get("/connect/youtube")
def connect_youtube():
    return {"auth_url": get_youtube_login_url()}

@router.get("/callback/youtube")
def callback_youtube(request: Request):
    return handle_youtube_callback(request)

@router.get("/connect/telegram")
def connect_telegram():
    return {"instructions": get_telegram_connect_instructions()}

@router.get("/callback/telegram")
def callback_telegram(request: Request):
    return handle_telegram_callback(request)
