from fastapi import APIRouter, Query, HTTPException
from services.ai_content import OpenRouterAI  # Updated import path
from typing import Literal
from pydantic import BaseModel, Field

class CaptionResponse(BaseModel):
    """Response model for caption generation.
    
    Contains the AI-generated caption text optimized for social media posts.
    """
    caption: str = Field(..., description="The AI-generated caption text")
    
    class Config:
        schema_extra = {
            "example": {
                "caption": "Exploring new horizons in tech today! The future is now, and we're building it together. #TechInnovation #FutureTech #SocialSuit #AI #DigitalTransformation"
            }
        }

router = APIRouter(
    prefix="/content", 
    tags=["AI Content"],
    description="Endpoints for AI-powered content generation using DeepSeek"
)

@router.get(
    "/generate", 
    response_model=CaptionResponse, 
    summary="Generate AI Caption",
    description="Generates an AI-powered caption based on the provided prompt, style, and hashtag preferences using DeepSeek's language model.",
    response_description="Returns the generated caption text optimized for social media."
)
async def generate_caption(
    prompt: str = Query(
        ..., 
        min_length=5, 
        max_length=500, 
        description="Content prompt for caption generation (topic, theme, or context)",
        example="Tech innovation and the future of work"
    ),
    style: Literal["casual", "formal", "funny"] = Query(
        ..., 
        description="Tone and style of the generated caption",
        example="casual"
    ),
    hashtags: int = Query(
        ..., 
        ge=0, 
        le=10, 
        description="Number of hashtags to include in the caption (0-10)",
        example=5
    ),
):
    """Generate an AI-powered caption for social media posts.
    
    This endpoint leverages DeepSeek's language model through OpenRouter to create
    engaging, platform-optimized captions based on your specifications.
    
    Args:
        prompt: The main topic or theme for the caption
        style: The tone of the caption (casual, formal, or funny)
        hashtags: Number of relevant hashtags to include
        
    Returns:
        A JSON object containing the generated caption
        
    Raises:
        HTTPException: If caption generation fails
    """
    try:
        ai = OpenRouterAI()
        caption = ai.generate_caption(prompt, style, hashtags)
        return {"caption": caption}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate caption: {str(e)}")

