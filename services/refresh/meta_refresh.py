import os
import requests
import logging

from services.database.database import get_db
from services.models.token_model import PlatformToken

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")

logger = logging.getLogger(__name__)  
def refresh_meta_token():
    """
    Refresh Facebook + Instagram tokens.
    Uses long-lived token exchange for Facebook Graph API.
    Logs each step.
    """
    db = next(get_db())
    tokens = db.query(PlatformToken).filter(
        PlatformToken.platform.in_(["facebook", "instagram"]),
        PlatformToken.refresh_token.isnot(None)
    ).all()

    for token in tokens:
        try:
            res = requests.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": META_APP_ID,
                    "client_secret": META_APP_SECRET,
                    "fb_exchange_token": token.refresh_token
                },
                timeout=15
            )

            res.raise_for_status()
            data = res.json()

            if "access_token" in data:
                token.access_token = data["access_token"]
                db.add(token)
                logger.info(f"[Meta Refresh] Token refreshed for user_id={token.user_id} ({token.platform})")
            else:
                logger.warning(f"[Meta Refresh] No access_token for user_id={token.user_id} — Response: {data}")

        except Exception as e:
            logger.exception(f"[Meta Refresh] Failed for user_id={token.user_id} ({token.platform}): {e}")

    db.commit()
    logger.info("[Meta Refresh] All tokens refreshed and committed.")