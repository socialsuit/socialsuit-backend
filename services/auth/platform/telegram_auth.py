# services/auth/telegram_auth.py

from fastapi import Request
from services.database.database import get_db
from services.models.token_model import PlatformToken

def get_telegram_connect_instructions() -> str:
    return (
        "1️⃣ Create a bot via BotFather.\n"
        "2️⃣ Copy the Bot Token.\n"
        "3️⃣ Add the bot as admin to your channel.\n"
        "4️⃣ Copy your channel @username.\n"
        "5️⃣ Submit bot_token + channel_id to SocialSuit."
    )

def handle_telegram_callback(request: Request):
    bot_token = request.query_params.get("bot_token")
    channel_id = request.query_params.get("channel_id")

    if not bot_token or not channel_id:
        return {"error": "Bot token or channel ID missing"}

    db = next(get_db())
    new_token = PlatformToken(
        user_id="PLACEHOLDER",
        platform="telegram",
        access_token=bot_token,
        channel_id=channel_id
    )
    db.add(new_token)
    db.commit()

    return {"msg": "Telegram connected!", "bot_token": bot_token, "channel_id": channel_id}
