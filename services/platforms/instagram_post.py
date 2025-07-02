# services/platforms/instagram_post.py

import requests

def call_instagram_post(user_token: dict, post_payload: dict):
    access_token = user_token["access_token"]
    ig_user_id = user_token["ig_user_id"]
    caption = post_payload.get("text", "")
    media_url = post_payload.get("media_url")
    media_type = post_payload.get("media_type", "image")

    # 1. Create container
    if media_type == "video":
        container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        payload = {
            "access_token": access_token,
            "media_type": "VIDEO",
            "video_url": media_url,
            "caption": caption
        }
    else:
        container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        payload = {
            "access_token": access_token,
            "image_url": media_url,
            "caption": caption
        }

    res = requests.post(container_url, data=payload)
    container_id = res.json().get("id")
    if not container_id:
        return {"error": "Failed to create container", "details": res.json()}

    # 2. Publish container
    publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
    publish_res = requests.post(publish_url, data={
        "creation_id": container_id,
        "access_token": access_token
    })

    return publish_res.json()