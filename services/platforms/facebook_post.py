# services/platforms/facebook_post.py

import requests

def call_facebook_post(user_token: dict, post_payload: dict):
    access_token = user_token["access_token"]
    page_id = user_token["page_id"]
    message = post_payload.get("text", "")
    media_url = post_payload.get("media_url")
    media_type = post_payload.get("media_type", "image")  # 'image' or 'video'

    if media_type == "video":
        # Facebook video upload endpoint
        video_endpoint = f"https://graph.facebook.com/{page_id}/videos"
        payload = {
            "access_token": access_token,
            "description": message,
            "file_url": media_url
        }
        response = requests.post(video_endpoint, data=payload)
    else:
        # Image or text
        post_endpoint = f"https://graph.facebook.com/{page_id}/photos" if media_url else f"https://graph.facebook.com/{page_id}/feed"
        payload = {
            "access_token": access_token,
            "message": message
        }
        if media_url:
            payload["url"] = media_url

        response = requests.post(post_endpoint, data=payload)

    return response.json()