# services/auth/linkedin_auth.py

import os
import requests
from fastapi import Request
from services.database.database import get_db
from services.models.token_model import PlatformToken

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI")

AUTH_URL = (
    "https://www.linkedin.com/oauth/v2/authorization"
    "?response_type=code"
    f"&client_id={LINKEDIN_CLIENT_ID}"
    f"&redirect_uri={LINKEDIN_REDIRECT_URI}"
    "&scope=w_member_social r_liteprofile"
)

TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"


def get_linkedin_login_url() -> str:
    return AUTH_URL


def handle_linkedin_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }

    res = requests.post(TOKEN_URL, data=data)
    res_json = res.json()

    access_token = res_json.get("access_token")

    if not access_token:
        return {"error": "No access token returned"}

    db = next(get_db())
    new_token = PlatformToken(
        user_id="PLACEHOLDER",
        platform="linkedin",
        access_token=access_token
    )
    db.add(new_token)
    db.commit()

    return {"msg": "LinkedIn connected!", "access_token": access_token}
