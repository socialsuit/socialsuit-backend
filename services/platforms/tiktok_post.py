# services/platforms/tiktok_post.py

import requests

def call_tiktok_post(user_token: dict, post_payload: dict):
    access_token = user_token["access_token"]
    open_id = user_token["open_id"]

    video_url = post_payload.get("media_url")
    description = post_payload.get("text", "")

    # TikTok Upload: Step 1: Upload video by URL
    upload_url = "https://open.tiktokapis.com/v2/post/publish/video/"

    payload = {
        "video_url": video_url,
        "text": description,
        "open_id": open_id
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    res = requests.post(upload_url, json=payload, headers=headers)
    return res.json()