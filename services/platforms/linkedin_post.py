# services/platforms/linkedin_post.py

import requests

def call_linkedin_post(user_token: dict, post_payload: dict):
    access_token = user_token["access_token"]
    text = post_payload.get("text", "")
    media_url = post_payload.get("media_url")
    media_type = post_payload.get("media_type", "image")

    owner = f"urn:li:person:{user_token['linkedin_id']}"

    if media_type == "video":
        return {"error": "LinkedIn video upload needs multipart. Use registerUpload & chunks."}
    else:
        api_url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {"Authorization": f"Bearer {access_token}",
                   "X-Restli-Protocol-Version": "2.0.0",
                   "Content-Type": "application/json"}

        body = {
            "author": owner,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE" if media_url else "NONE",
                    "media": [{
                        "status": "READY",
                        "description": {"text": text},
                        "originalUrl": media_url,
                        "title": {"text": "Social Suit Upload"}
                    }] if media_url else []
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }

        res = requests.post(api_url, json=body, headers=headers)
        return res.json()