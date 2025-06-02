import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import APIRouter
from services.ai_content import OpenRouterAI

router = APIRouter()

@router.get("/generate")
def gen(prompt: str):
    ai = OpenRouterAI()
    caption = ai.generate_caption(prompt)
    return {"caption": caption}  # ✅ wrap the result in a JSON-friendly format

