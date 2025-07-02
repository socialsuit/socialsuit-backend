# services/platforms/telegram_post.py

import requests

def call_telegram_api(user_token: dict, post_payload: dict):
    bot_token = user_token["access_token"]
    channel_id = user_token["channel_id"]

    text = post_payload.get("text", "")
    media_url = post_payload.get("media_url")
    media_type = post_payload.get("media_type", "image")

    if media_type == "video":
        api_url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
        payload = {
            "chat_id": channel_id,
            "video": media_url,
            "caption": text
        }
    else:
        api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        payload = {
            "chat_id": channel_id,
            "photo": media_url,
            "caption": text
        }

    res = requests.post(api_url, data=payload)
    return res.json()