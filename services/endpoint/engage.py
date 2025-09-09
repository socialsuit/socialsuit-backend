from fastapi import APIRouter, Body, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from services.auto_engagement import auto_engage
from services.auth.auth_guard import auth_required
from services.models.user_model import User
from services.database.database import get_db
from sqlalchemy.orm import Session

class EngagementRequest(BaseModel):
    """
    Request model for auto-engagement processing.
    
    Contains the message to be processed and optional context information.
    """
    message: str = Field(..., description="The message to process for auto-engagement")
    platform: Optional[str] = Field("general", description="The platform where the message originated")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context for processing")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What are the pricing options for Social Suit?",
                "platform": "twitter",
                "context": {
                    "user_tier": "premium",
                    "previous_interactions": 3,
                    "language": "en"
                }
            }
        }

class EngagementResponse(BaseModel):
    """
    Response model for auto-engagement processing.
    
    Contains the generated reply and metadata about the engagement.
    """
    reply: str = Field(..., description="The auto-generated reply message")
    action: str = Field(..., description="The suggested backend action")
    priority: str = Field(..., description="The priority level of the response")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata about the engagement")
    
    class Config:
        schema_extra = {
            "example": {
                "reply": "Thanks for your interest in Social Suit! Our Premium plan starts at $29/month and includes all core features plus advanced analytics. Would you like me to send you our full pricing guide?",
                "action": "trigger_pricing_flow",
                "priority": "high",
                "metadata": {
                    "detected_intent": "pricing",
                    "confidence_score": 0.92,
                    "user_tier": "premium",
                    "platform": "twitter",
                    "source": "custom",
                    "timestamp": "2023-08-15T12:34:56.789Z"
                }
            }
        }

# Create router with appropriate tag and description
router = APIRouter(
    prefix="/engage",
    tags=["Engagement"],
    description="Endpoints for automated engagement and response generation"
)

@router.post(
    "/reply",
    response_model=EngagementResponse,
    summary="Generate Auto-Reply",
    description="Processes a message and generates an appropriate automated response using hybrid logic",
    response_description="Returns the generated reply and engagement metadata"
)
async def reply(
    engagement_data: EngagementRequest = Body(
        ...,
        description="The message and context for auto-engagement processing"
    ),
    current_user: User = Depends(auth_required),
    db: Session = Depends(get_db)
):
    """
    Generate an automated reply to a message using hybrid logic.
    
    This endpoint processes an incoming message using a hybrid approach:
    1. First checks for custom brand replies in the database
    2. If no custom reply is found, uses DeepSeek AI via OpenRouter API
    
    The response is personalized based on the user's tier and platform context.
    
    Args:
        engagement_data: The message and context information
        current_user: The authenticated user (injected by dependency)
        db: Database session
        
    Returns:
        A JSON object with the generated reply and engagement metadata
    """
    # Get user tier from context or default to "free"
    user_tier = engagement_data.context.get("user_tier", "free")
    
    # Process the message using the auto_engage service
    result = await auto_engage(
        message=engagement_data.message,
        platform=engagement_data.platform or "general",
        user_type=user_tier,
        context=engagement_data.context,
        user_id=str(current_user.id)
    )
    
    return result
