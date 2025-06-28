import requests

def call_facebook_post(user_token: dict, post_payload: dict):
    access_token = user_token.get("access_token")
    page_id = user_token.get("page_id")

    message = post_payload.get("caption")
    image_url = post_payload.get("image_url")

    url = f"https://graph.facebook.com/{page_id}/photos"
    payload = {
        "url": image_url,
        "caption": message,
        "access_token": access_token
    }

    response = requests.post(url, data=payload)
    return response.json()