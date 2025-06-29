# services/auth/meta_auth.py

import os
import requests
from fastapi import Request
from services.database.database import get_db
from services.models.token_model import PlatformToken

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
REDIRECT_URI = os.getenv("META_REDIRECT_URI")

AUTH_URL = (
    "https://www.facebook.com/v18.0/dialog/oauth"
    "?client_id={app_id}&redirect_uri={redirect_uri}"
    "&scope=pages_manage_posts,pages_read_engagement,instagram_basic,pages_show_list"
)

TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"


def get_meta_login_url() -> str:
    return AUTH_URL.format(app_id=META_APP_ID, redirect_uri=REDIRECT_URI)


def handle_meta_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}

    params = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    res = requests.get(TOKEN_URL, params=params)
    res_json = res.json()

    access_token = res_json.get("access_token")

    if not access_token:
        return {"error": "No access token returned"}

    db = next(get_db())
    new_token = PlatformToken(
        user_id="PLACEHOLDER",
        platform="meta",  # Both FB & IG covered
        access_token=access_token
    )
    db.add(new_token)
    db.commit()

    return {"msg": "Facebook & Instagram connected!", "access_token": access_token}
