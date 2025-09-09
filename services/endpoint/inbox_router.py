from fastapi import APIRouter, Body, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import httpx
import json
import logging

from services.auth.auth_guard import auth_required
from services.models.user_model import User
from services.database.mongodb import MongoDBManager
from core.config import settings

# Create router
router = APIRouter(
    prefix="",
    tags=["inbox"],
    responses={404: {"description": "Not found"}},
)

# Constants
COMMENTS_COLLECTION = "comments"

# Comment schema model
class CommentBase(BaseModel):
    """
    Base model for comment data.
    """
    platform: str = Field(..., description="The platform where the comment originated (twitter, discord, telegram, farcaster, etc.)")
    user: str = Field(..., description="The user who made the comment")
    comment_text: str = Field(..., description="The text content of the comment")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the comment was created")
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "twitter",
                "user": "@user123",
                "comment_text": "When will you release the new feature?",
                "timestamp": "2023-08-15T12:34:56.789Z"
            }
        }

class CommentCreate(CommentBase):
    """
    Model for creating a new comment.
    """
    pass

class CommentResponse(CommentBase):
    """
    Model for comment responses including ID and category.
    """
    id: str = Field(..., description="Unique identifier for the comment")
    category: str = Field("all", description="Classification category: all, relevant, community, or spam")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "platform": "twitter",
                "user": "@user123",
                "comment_text": "When will you release the new feature?",
                "timestamp": "2023-08-15T12:34:56.789Z",
                "category": "relevant"
            }
        }

class ClassificationRequest(BaseModel):
    """
    Model for requesting comment classification.
    """
    comment_id: str = Field(..., description="ID of the comment to classify")
    
    class Config:
        schema_extra = {
            "example": {
                "comment_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class ClassificationResponse(BaseModel):
    """
    Model for classification response.
    """
    comment_id: str = Field(..., description="ID of the classified comment")
    category: str = Field(..., description="Classification result: relevant, community, or spam")
    confidence: float = Field(..., description="Confidence score of the classification")
    
    class Config:
        schema_extra = {
            "example": {
                "comment_id": "550e8400-e29b-41d4-a716-446655440000",
                "category": "relevant",
                "confidence": 0.92
            }
        }


# GET endpoints
@router.get(
    "/all",
    response_model=List[CommentResponse],
    summary="Get All Comments",
    description="Retrieves all comments from all platforms",
    response_description="Returns a list of all comments"
)
async def get_all_comments(
    skip: int = Query(0, description="Number of comments to skip"),
    limit: int = Query(50, description="Maximum number of comments to return"),
    current_user: User = Depends(auth_required)
):
    """
    Retrieve all comments from the database.
    
    Args:
        skip: Number of comments to skip (pagination)
        limit: Maximum number of comments to return (pagination)
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        A list of comments with their metadata
    """
    try:
        # Query MongoDB for all comments
        comments = await MongoDBManager.find_with_options(
            collection=COMMENTS_COLLECTION,
            query={},  # Empty query to get all comments
            sort=[("timestamp", -1)],  # Sort by timestamp descending (newest first)
            skip=skip,
            limit=limit
        )
        
        # Convert MongoDB documents to Pydantic models
        return [CommentResponse(**comment) for comment in comments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve comments: {str(e)}")


@router.get(
    "/filter/{category}",
    response_model=List[CommentResponse],
    summary="Get Filtered Comments",
    description="Retrieves comments filtered by category (relevant, community, spam)",
    response_description="Returns a list of filtered comments"
)
async def get_filtered_comments(
    category: str,
    skip: int = Query(0, description="Number of comments to skip"),
    limit: int = Query(50, description="Maximum number of comments to return"),
    current_user: User = Depends(auth_required)
):
    """
    Retrieve comments filtered by category.
    
    Args:
        category: The category to filter by (relevant, community, spam)
        skip: Number of comments to skip (pagination)
        limit: Maximum number of comments to return (pagination)
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        A list of filtered comments with their metadata
    """
    # Validate category
    valid_categories = ["relevant", "community", "spam"]
    if category not in valid_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    try:
        # Query MongoDB for filtered comments
        comments = await MongoDBManager.find_with_options(
            collection=COMMENTS_COLLECTION,
            query={"category": category},
            sort=[("timestamp", -1)],  # Sort by timestamp descending (newest first)
            skip=skip,
            limit=limit
        )
        
        # Convert MongoDB documents to Pydantic models
        return [CommentResponse(**comment) for comment in comments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve filtered comments: {str(e)}")


# POST endpoint for adding a new comment
@router.post(
    "/add",
    response_model=CommentResponse,
    summary="Add New Comment",
    description="Adds a new comment to the database",
    response_description="Returns the added comment with its ID and metadata"
)
async def add_comment(
    comment: CommentCreate = Body(..., description="The comment to add"),
    current_user: User = Depends(auth_required)
):
    """
    Add a new comment to the database.
    
    Args:
        comment: The comment data to add
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        The added comment with its ID and metadata
    """
    try:
        # Create a new comment document
        new_comment = comment.dict()
        
        # Add ID and default category
        new_comment["id"] = str(uuid.uuid4())
        new_comment["category"] = "all"  # Default category before classification
        
        # Ensure timestamp is a datetime object
        if isinstance(new_comment["timestamp"], str):
            new_comment["timestamp"] = datetime.fromisoformat(new_comment["timestamp"].replace('Z', '+00:00'))
        
        # Insert into MongoDB
        await MongoDBManager._db[COMMENTS_COLLECTION].insert_one(new_comment)
        
        # Return the created comment
        return CommentResponse(**new_comment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")


# POST endpoint for classifying a comment
@router.post(
    "/classify",
    response_model=ClassificationResponse,
    summary="Classify Comment",
    description="Classifies a comment using OpenRouter DeepSeek API",
    response_description="Returns the classification result"
)
async def classify_comment(
    classification_request: ClassificationRequest = Body(..., description="The comment ID to classify"),
    current_user: User = Depends(auth_required)
):
    """
    Classify a comment using OpenRouter DeepSeek API.
    
    Args:
        classification_request: The request containing the comment ID to classify
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        The classification result with category and confidence score
    """
    comment_id = classification_request.comment_id
    
    try:
        # Retrieve the comment from MongoDB
        comment = await MongoDBManager._db[COMMENTS_COLLECTION].find_one({"id": comment_id})
        
        if not comment:
            raise HTTPException(status_code=404, detail=f"Comment with ID {comment_id} not found")
        
        # Get the comment text for classification
        comment_text = comment.get("comment_text", "")
        
        # Call OpenRouter DeepSeek API for classification
        category, confidence = await classify_with_deepseek(comment_text)
        
        # Update the comment with the classification result
        await MongoDBManager._db[COMMENTS_COLLECTION].update_one(
            {"id": comment_id},
            {"$set": {"category": category}}
        )
        
        # Return the classification result
        return ClassificationResponse(
            comment_id=comment_id,
            category=category,
            confidence=confidence
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to classify comment: {str(e)}")


async def classify_with_deepseek(comment_text: str) -> tuple[str, float]:
    """
    Classify a comment using OpenRouter DeepSeek API with robust fallback logic.
    
    Args:
        comment_text: The text of the comment to classify
        
    Returns:
        A tuple containing the category and confidence score
    """
    # Define a simple keyword-based fallback classifier
    def fallback_classify(text: str) -> tuple[str, float]:
        text = text.lower()
        
        # Spam indicators
        spam_keywords = [
            "buy now", "click here", "free offer", "limited time", "discount code",
            "www.", "http:", "https:", "earn money", "make money", "$$$",
            "casino", "lottery", "viagra", "cialis", "weight loss", "diet pill"
        ]
        
        # Community indicators
        community_keywords = [
            "love your content", "great page", "following you", "big fan",
            "keep it up", "love your work", "awesome profile", "nice feed"
        ]
        
        # Check for spam first (higher priority)
        for keyword in spam_keywords:
            if keyword in text:
                return "spam", 0.8
        
        # Then check for community comments
        for keyword in community_keywords:
            if keyword in text:
                return "community", 0.8
        
        # Default to relevant if no patterns match
        return "relevant", 0.6
    
    # Prepare the request to OpenRouter API
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://social-suit.com",
        "X-Title": "Social Suit Comment Classification"
    }
    
    # Prepare the prompt for classification
    system_prompt = (
        "You are an AI that classifies social media comments into one of three categories:\n"
        "1. 'spam': Low-value comments like 'hello', 'gm', 'moon', or repeated text\n"
        "2. 'relevant': Questions about product, roadmap, pricing, events, or specific inquiries\n"
        "3. 'community': Compliments, casual positive engagement, or general community interaction\n\n"
        "Respond with ONLY the category name (spam, relevant, or community) and a confidence score between 0 and 1."
        "Format your response exactly like this: 'category: [category], confidence: [score]'"
    )
    
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": comment_text}
        ],
        "temperature": 0.3  # Lower temperature for more consistent classification
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:  # Reduced timeout for better UX
            response = await client.post(
                settings.OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extract category and confidence from the response
            # Expected format: "category: [category], confidence: [score]"
            try:
                category_part = ai_response.split("category:")[1].split(",")[0].strip().lower()
                confidence_part = ai_response.split("confidence:")[1].strip()
                confidence = float(confidence_part)
                
                # Validate the category
                if category_part in ["spam", "relevant", "community"]:
                    category = category_part
                else:
                    # Use fallback classifier if AI response doesn't match expected categories
                    logging.warning(f"Unexpected DeepSeek classification response: {ai_response}. Using fallback.")
                    return fallback_classify(comment_text)
                    
                return category, confidence
            except (IndexError, ValueError):
                # If parsing fails, use fallback classifier
                logging.warning(f"Failed to parse DeepSeek response: {ai_response}. Using fallback.")
                return fallback_classify(comment_text)
    except httpx.TimeoutException as e:
        logging.warning(f"DeepSeek API timeout during comment classification: {str(e)}")
        # Use fallback classifier on timeout
        return fallback_classify(comment_text)
        
    except httpx.HTTPStatusError as e:
        logging.error(f"DeepSeek API HTTP error during classification: {e.response.status_code} - {str(e)}")
        # Use fallback classifier on HTTP errors
        return fallback_classify(comment_text)
        
    except Exception as e:
        logging.error(f"Error calling OpenRouter API: {str(e)}")
        # Use fallback classifier for any other errors
        return fallback_classify(comment_text)