import requests

def call_instagram_post(user_token: dict, post_payload: dict):
    access_token = user_token.get("access_token")
    ig_user_id = user_token.get("ig_user_id")

    image_url = post_payload.get("image_url")
    caption = post_payload.get("caption")

    create_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
    publish_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"

    create_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }

    media_res = requests.post(create_url, data=create_payload).json()
    creation_id = media_res.get("id")

    if not creation_id:
        return {"error": "Media creation failed", "details": media_res}

    publish_payload = {"creation_id": creation_id, "access_token": access_token}
    publish_res = requests.post(publish_url, data=publish_payload).json()

    return publish_res