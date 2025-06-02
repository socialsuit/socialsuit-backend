from fastapi import APIRouter
from services.analytics import get_insights

router = APIRouter()

@router.get("/analytics")
def insights(platform: str = "all"):
    return get_insights(platform)
