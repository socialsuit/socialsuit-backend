from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pytz  # for timezone validation
from services.smart_schedule import smart_schedule

VALID_PLATFORMS = ["facebook", "instagram", "twitter", "linkedin"]

router = APIRouter()

@router.get("/schedule")
def get_schedule(
    platform: str = Query(..., min_length=1),
    content_type: Optional[str] = Query("post"),
    timezone: Optional[str] = Query("UTC"),
    audience_location: Optional[str] = Query(None)
):
    # Validate platform
    if platform.lower() not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail="Invalid platform provided.")

    # Validate timezone
    if timezone not in pytz.all_timezones:
        raise HTTPException(status_code=400, detail="Invalid timezone provided.")

    try:
        return smart_schedule(
            platform=platform,
            content_type=content_type,
            timezone=timezone,
            audience_location=audience_location
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

