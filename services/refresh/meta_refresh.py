# services/refresh/meta_refresh.py

import os
import requests
from services.database.database import get_db
from services.models.token_model import PlatformToken

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")

def refresh_meta_token():
    db = next(get_db())
    tokens = db.query(PlatformToken).filter(
        PlatformToken.platform.in_(["facebook", "instagram"]),
        PlatformToken.refresh_token.isnot(None)
    ).all()

    for token in tokens:
        # Facebook long-lived token: same endpoint
        res = requests.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "fb_exchange_token": token.refresh_token
            }
        )
        data = res.json()
        if "access_token" in data:
            token.access_token = data["access_token"]
            db.add(token)

    db.commit()