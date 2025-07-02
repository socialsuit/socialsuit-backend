# services/refresh/twitter_refresh.py

import os
import requests
from services.database.database import get_db
from services.models.token_model import PlatformToken

TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

def refresh_twitter_token():
    db = next(get_db())
    tokens = db.query(PlatformToken).filter(
        PlatformToken.platform == "twitter",
        PlatformToken.refresh_token.isnot(None)
    ).all()

    for token in tokens:
        data = {
            "client_id": TWITTER_CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        res = requests.post(
            "https://api.twitter.com/2/oauth2/token",
            data=data,
            headers=headers,
            auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
        )

        data = res.json()
        if "access_token" in data:
            token.access_token = data["access_token"]
            token.refresh_token = data.get("refresh_token", token.refresh_token)
            db.add(token)

    db.commit()