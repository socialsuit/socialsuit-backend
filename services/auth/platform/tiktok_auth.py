# services/auth/tiktok_auth.py

import os
import requests
from fastapi import Request
from services.database.database import get_db
from services.models.token_model import PlatformToken

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")

AUTH_URL = (
    "https://www.tiktok.com/v2/auth/authorize/"
    "?client_key={client_key}"
    "&response_type=code"
    "&scope=user.info.basic,video.upload"
    "&redirect_uri={redirect_uri}"
)

TOKEN_URL = "https://open-api.tiktok.com/v2/oauth/token/"


def get_tiktok_login_url() -> str:
    return AUTH_URL.format(client_key=TIKTOK_CLIENT_KEY, redirect_uri=TIKTOK_REDIRECT_URI)


def handle_tiktok_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}

    data = {
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": TIKTOK_REDIRECT_URI
    }

    res = requests.post(TOKEN_URL, data=data)
    res_json = res.json()

    access_token = res_json.get("access_token")

    if not access_token:
        return {"error": "No access token returned"}

    db = next(get_db())
    new_token = PlatformToken(
        user_id="PLACEHOLDER",
        platform="tiktok",
        access_token=access_token
    )
    db.add(new_token)
    db.commit()

    return {"msg": "TikTok connected!", "access_token": access_token}
