from fastapi import APIRouter
from services.ai_content import OpenRouterAI
from fastapi import Query, HTTPException
from typing import Literal

router = APIRouter()

@router.get("/generate")
def gen(
    prompt: str = Query(..., min_length=5, max_length=500),
    style: Literal["casual", "formal", "funny"] = Query(...),
    hashtags: int = Query(..., ge=0, le=10),
):
    ai = OpenRouterAI()
    caption = ai.generate_caption(prompt)
    return {"caption": caption}

