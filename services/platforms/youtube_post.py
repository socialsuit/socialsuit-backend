# services/platforms/youtube_post.py

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import requests

def call_youtube_post(user_token: dict, post_payload: dict):
    credentials = user_token["credentials"]
    title = post_payload.get("title", "Untitled Video")
    description = post_payload.get("text", "")
    media_url = post_payload.get("media_url")

    youtube = build("youtube", "v3", credentials=credentials)
    video_data = requests.get(media_url).content

    media = MediaIoBaseUpload(io.BytesIO(video_data), mimetype="video/*", chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["socialsuit"],
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
    return response
