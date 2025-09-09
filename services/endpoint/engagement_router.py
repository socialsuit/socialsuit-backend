from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from services.database.database import get_db
from services.models.custom_reply_model import CustomReply
from services.auth.auth_guard import auth_required
from services.models.user_model import User

# Pydantic models for request/response
class CustomReplyBase(BaseModel):
    intent: str = Field(..., description="The intent or category of the reply")
    keyword: str = Field(..., description="The keyword that triggers this reply")
    custom_reply: str = Field(..., description="The custom reply text")
    platform: str = Field(..., description="The platform this reply is for (twitter, instagram, etc.)")

class CustomReplyCreate(CustomReplyBase):
    pass

class CustomReplyUpdate(CustomReplyBase):
    intent: Optional[str] = None
    keyword: Optional[str] = None
    custom_reply: Optional[str] = None
    platform: Optional[str] = None

class CustomReplyResponse(CustomReplyBase):
    id: int
    brand_id: str
    
    class Config:
        orm_mode = True

# Create router
router = APIRouter(
    prefix="/custom-replies",
    tags=["Engagement"],
    description="Endpoints for managing custom brand replies"
)

@router.post(
    "/",
    response_model=CustomReplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Custom Reply",
    description="Create a new custom reply for a specific brand"
)
async def create_custom_reply(
    custom_reply: CustomReplyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Create a new custom reply for automated engagement."""
    db_custom_reply = CustomReply(
        brand_id=str(current_user.id),  # Use the authenticated user's ID as the brand ID
        intent=custom_reply.intent,
        keyword=custom_reply.keyword,
        custom_reply=custom_reply.custom_reply,
        platform=custom_reply.platform
    )
    
    db.add(db_custom_reply)
    db.commit()
    db.refresh(db_custom_reply)
    
    return db_custom_reply

@router.get(
    "/",
    response_model=List[CustomReplyResponse],
    summary="Get Custom Replies",
    description="Get all custom replies for the authenticated brand"
)
async def get_custom_replies(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    intent: Optional[str] = Query(None, description="Filter by intent"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Get all custom replies for the authenticated brand with optional filtering."""
    query = db.query(CustomReply).filter(CustomReply.brand_id == str(current_user.id))
    
    if platform:
        query = query.filter(CustomReply.platform == platform)
    
    if intent:
        query = query.filter(CustomReply.intent == intent)
    
    return query.all()

@router.get(
    "/{reply_id}",
    response_model=CustomReplyResponse,
    summary="Get Custom Reply",
    description="Get a specific custom reply by ID"
)
async def get_custom_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Get a specific custom reply by ID."""
    db_custom_reply = db.query(CustomReply).filter(
        CustomReply.id == reply_id,
        CustomReply.brand_id == str(current_user.id)
    ).first()
    
    if not db_custom_reply:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom reply not found"
        )
    
    return db_custom_reply

@router.put(
    "/{reply_id}",
    response_model=CustomReplyResponse,
    summary="Update Custom Reply",
    description="Update a specific custom reply by ID"
)
async def update_custom_reply(
    reply_id: int,
    custom_reply: CustomReplyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Update a specific custom reply by ID."""
    db_custom_reply = db.query(CustomReply).filter(
        CustomReply.id == reply_id,
        CustomReply.brand_id == str(current_user.id)
    ).first()
    
    if not db_custom_reply:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom reply not found"
        )
    
    # Update fields if provided
    if custom_reply.intent is not None:
        db_custom_reply.intent = custom_reply.intent
    
    if custom_reply.keyword is not None:
        db_custom_reply.keyword = custom_reply.keyword
    
    if custom_reply.custom_reply is not None:
        db_custom_reply.custom_reply = custom_reply.custom_reply
    
    if custom_reply.platform is not None:
        db_custom_reply.platform = custom_reply.platform
    
    db.commit()
    db.refresh(db_custom_reply)
    
    return db_custom_reply

@router.delete(
    "/{reply_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Custom Reply",
    description="Delete a specific custom reply by ID"
)
async def delete_custom_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Delete a specific custom reply by ID."""
    db_custom_reply = db.query(CustomReply).filter(
        CustomReply.id == reply_id,
        CustomReply.brand_id == str(current_user.id)
    ).first()
    
    if not db_custom_reply:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom reply not found"
        )
    
    db.delete(db_custom_reply)
    db.commit()
    
    return None