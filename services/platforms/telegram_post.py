# services/scheduler/platforms/telegram_post.py

import requests

def call_telegram_api(user_token: dict, post_payload: dict):
    """
    user_token = {
        "bot_token": "...",
        "channel_id": "@channelusername"
    }
    post_payload = {
        "text": "Your message here",
        "parse_mode": "HTML"  # Optional
    }
    """
    bot_token = user_token["bot_token"]
    channel_id = user_token["channel_id"]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": channel_id,
        "text": post_payload["text"],
        "parse_mode": post_payload.get("parse_mode", "HTML")
    }

    res = requests.post(url, json=payload)
    return res.json()
