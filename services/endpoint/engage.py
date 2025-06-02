from fastapi import APIRouter
from services.auto_engagement import auto_engage

router = APIRouter()

@router.post("/reply")
def reply(message: str):
    return auto_engage(message)
