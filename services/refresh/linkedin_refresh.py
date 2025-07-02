# services/refresh/linkedin_refresh.py

import os
import requests
from services.database.database import get_db
from services.models.token_model import PlatformToken

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

def refresh_linkedin_token():
    db = next(get_db())
    tokens = db.query(PlatformToken).filter(
        PlatformToken.platform == "linkedin",
        PlatformToken.refresh_token.isnot(None)
    ).all()

    for token in tokens:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET
        }

        res = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data=data
        )

        data = res.json()
        if "access_token" in data:
            token.access_token = data["access_token"]
            db.add(token)

    db.commit()