from fastapi import APIRouter, Query
from typing import Optional
from services.thumbnail import ThumbnailGenerator

router = APIRouter()
thumbnail_gen = ThumbnailGenerator()

@router.get("/generate-thumbnail")
def generate_thumbnail(
    query: str = Query(..., description="Search term for thumbnail image"),
    platform: Optional[str] = Query("universal", description="Target platform like instagram_post, twitter, etc.")
):
    return thumbnail_gen.fetch_thumbnail(query=query, platform=platform)
