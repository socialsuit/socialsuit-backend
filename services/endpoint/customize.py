from fastapi import APIRouter
from pydantic import BaseModel
from services.post_customizer import customize

router = APIRouter()

class CustomizeRequest(BaseModel):
    content: str
    platform: str

@router.post("/customize")
def customize_post(req: CustomizeRequest):
    return customize(req.content, req.platform)
