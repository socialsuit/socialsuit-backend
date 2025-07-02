# services/platforms/farcaster_post.py

import requests

def call_farcaster_post(user_token: dict, post_payload: dict):
    address = user_token["wallet_address"]
    signature = user_token["signature"]

    text = post_payload.get("text", "")
    media_url = post_payload.get("media_url")

    # Farcaster mostly uses Warpcast or hubs that take frame or link:
    farcaster_api = "https://farcaster-api.example.com/post"

    payload = {
        "address": address,
        "signature": signature,
        "content": f"{text}\n{media_url}" if media_url else text
    }

    res = requests.post(farcaster_api, json=payload)
    return res.json()