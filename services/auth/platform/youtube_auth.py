# services/auth/youtube_auth.py

import os
import requests
from fastapi import Request
from services.database.database import get_db
from services.models.token_model import PlatformToken

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI")

AUTH_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
    "?client_id={client_id}"
    "&redirect_uri={redirect_uri}"
    "&response_type=code"
    "&scope=https://www.googleapis.com/auth/youtube.upload"
    "&access_type=offline"
)

TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_youtube_login_url() -> str:
    return AUTH_URL.format(client_id=YOUTUBE_CLIENT_ID, redirect_uri=YOUTUBE_REDIRECT_URI)


def handle_youtube_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}

    data = {
        "code": code,
        "client_id": YOUTUBE_CLIENT_ID,
        "client_secret": YOUTUBE_CLIENT_SECRET,
        "redirect_uri": YOUTUBE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    res = requests.post(TOKEN_URL, data=data)
    res_json = res.json()

    access_token = res_json.get("access_token")
    refresh_token = res_json.get("refresh_token")

    if not access_token:
        return {"error": "No access token returned"}

    db = next(get_db())
    new_token = PlatformToken(
        user_id="PLACEHOLDER",
        platform="youtube",
        access_token=access_token,
        refresh_token=refresh_token
    )
    db.add(new_token)
    db.commit()

    return {"msg": "YouTube connected!", "access_token": access_token}
