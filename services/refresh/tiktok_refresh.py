# services/refresh/tiktok_refresh.py

import os
import requests
from services.database.database import get_db
from services.models.token_model import PlatformToken

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")

def refresh_tiktok_token():
    db = next(get_db())
    tokens = db.query(PlatformToken).filter(
        PlatformToken.platform == "tiktok",
        PlatformToken.refresh_token.isnot(None)
    ).all()

    for token in tokens:
        data = {
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token
        }

        res = requests.post(
            "https://open-api.tiktok.com/oauth/refresh_token/",
            data=data
        )

        data = res.json()
        if "access_token" in data:
            token.access_token = data["access_token"]
            token.refresh_token = data.get("refresh_token", token.refresh_token)
            db.add(token)

    db.commit()