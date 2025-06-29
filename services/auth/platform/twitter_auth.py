# services/auth/twitter_auth.py

import os
import requests
from fastapi import Request
from services.database.database import get_db
from services.models.token_model import PlatformToken

TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI")

AUTH_URL = (
    "https://twitter.com/i/oauth2/authorize"
    "?response_type=code"
    f"&client_id={TWITTER_CLIENT_ID}"
    f"&redirect_uri={TWITTER_REDIRECT_URI}"
    "&scope=tweet.read tweet.write users.read offline.access"
    "&state=state"
    "&code_challenge=challenge"
    "&code_challenge_method=plain"
)

TOKEN_URL = "https://api.twitter.com/2/oauth2/token"


def get_twitter_login_url() -> str:
    return AUTH_URL


def handle_twitter_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}

    data = {
        "client_id": TWITTER_CLIENT_ID,
        "client_secret": TWITTER_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": TWITTER_REDIRECT_URI,
        "code_verifier": "challenge"
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(TOKEN_URL, data=data, headers=headers)
    res_json = res.json()

    access_token = res_json.get("access_token")
    refresh_token = res_json.get("refresh_token")

    if not access_token:
        return {"error": "No access token returned"}

    db = next(get_db())
    new_token = PlatformToken(
        user_id="PLACEHOLDER",
        platform="twitter",
        access_token=access_token,
        refresh_token=refresh_token
    )
    db.add(new_token)
    db.commit()

    return {"msg": "Twitter connected!", "access_token": access_token}
