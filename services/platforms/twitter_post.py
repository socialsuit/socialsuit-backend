# services/platforms/twitter_post.py

import os
import requests

def call_twitter_post(user_token: dict, post_payload: dict):
    access_token = user_token["access_token"]
    media_url = post_payload.get("media_url")
    text = post_payload.get("text", "")
    media_type = post_payload.get("media_type", "image")

    headers = {"Authorization": f"Bearer {access_token}"}

    media_id = None

    if media_url:
        # Upload media in chunks if video
        if media_type == "video":
            # Twitter has a 3-step chunked upload: INIT, APPEND, FINALIZE
            # For simplicity, assume small file:
            upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            init = requests.post(upload_url, data={
                "command": "INIT",
                "media_type": "video/mp4",
                "total_bytes": str(len(media_url))
            }, headers=headers)
            media_id = init.json().get("media_id_string")
            # You’d add APPEND & FINALIZE here (or use tweepy)
        else:
            # Single image upload
            upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            file_res = requests.post(upload_url, files={"media": requests.get(media_url).content}, headers=headers)
            media_id = file_res.json().get("media_id_string")

    post_url = "https://api.twitter.com/1.1/statuses/update.json"
    payload = {"status": text}
    if media_id:
        payload["media_ids"] = media_id

    res = requests.post(post_url, params=payload, headers=headers)
    return res.json()