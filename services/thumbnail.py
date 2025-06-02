import os
import time
import requests
from dotenv import load_dotenv
from typing import Dict, Optional
from urllib.parse import quote

load_dotenv()

class ThumbnailGenerator:
    def __init__(self):
        self.UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
        self.BASE_URL = "https://api.unsplash.com/photos/random"
        self.CACHE = {}  # {cache_key: (timestamp, result)}

    def _get_platform_params(self, platform: str) -> Dict:
        """Returns optimized parameters for each platform"""
        params = {
            "universal": {"orientation": "landscape"},
            "instagram_post": {"w": 1080, "h": 1350, "orientation": "portrait"},
            "instagram_story": {"w": 1080, "h": 1920},
            "twitter": {"w": 1200, "h": 675},
            "linkedin": {"w": 1200, "h": 627},
            "pinterest": {"w": 1000, "h": 1500},
            "facebook": {"w": 1200, "h": 630},
            "youtube_thumbnail": {"w": 1280, "h": 720}
        }
        return params.get(platform, params["universal"])

    def fetch_thumbnail(
        self,
        query: str,
        platform: str = "universal",
        cache_timeout: int = 3600  # seconds
    ) -> Dict[str, Optional[str]]:
        """
        Fetches optimized thumbnails for all social platforms
        """
        cache_key = f"{platform}_{quote(query)}"
        now = time.time()

        # Check and return from cache if valid
        if cache_key in self.CACHE:
            timestamp, cached_result = self.CACHE[cache_key]
            if now - timestamp < cache_timeout:
                return cached_result

        try:
            params = {
                "query": query,
                "client_id": self.UNSPLASH_ACCESS_KEY,
                **self._get_platform_params(platform)
            }

            response = requests.get(self.BASE_URL, params=params, timeout=10)

            if response.status_code == 403:
                return {
                    "error": "❌ Unsplash API quota exceeded. Please wait before making more requests.",
                    "platform": platform,
                    "query": query
                }

            data = response.json()

            result = {
                "image_url": data["urls"]["regular"],
                "photographer": data["user"]["name"],
                "source": data["links"]["html"],
                "platform": platform,
                "download_link": data["links"].get("download_location"),
                "color_palette": data.get("color"),
                "attribution_text": f"Photo by {data['user']['name']} on Unsplash"
            }

            self.CACHE[cache_key] = (now, result)
            return result

        except requests.exceptions.RequestException as e:
            return {
                "error": f"❌ API request failed: {str(e)}",
                "platform": platform,
                "query": query
            }
        except KeyError as e:
            return {
                "error": f"❌ Invalid API response format: {str(e)}",
                "platform": platform
            }
