# services/refresh/youtube_refresh.py

import os
import requests
from services.database.database import get_db
from services.models.token_model import PlatformToken

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

def refresh_youtube_token():
    db = next(get_db())
    tokens = db.query(PlatformToken).filter(
        PlatformToken.platform == "youtube",
        PlatformToken.refresh_token.isnot(None)
    ).all()

    for token in tokens:
        data = {
            "client_id": YOUTUBE_CLIENT_ID,
            "client_secret": YOUTUBE_CLIENT_SECRET,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token"
        }

        res = requests.post(
            "https://oauth2.googleapis.com/token",
            data=data
        )

        data = res.json()
        if "access_token" in data:
            token.access_token = data["access_token"]
            db.add(token)

    db.commit()