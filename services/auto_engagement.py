from datetime import datetime
import re
import httpx
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from core.config import settings
from services.database.database import get_db_session
from services.models.custom_reply_model import CustomReply

# Configure logging
logger = logging.getLogger(__name__)

async def auto_engage(message: str, platform: str = "general", user_type: str = "free", 
                     context: Dict[str, Any] = None, user_id: str = None) -> dict:
    """
    Advanced hybrid auto-responder for Social Suit that combines:
    - Custom brand replies from database
    - DeepSeek AI responses via OpenRouter API
    
    Args:
        message: User's input text
        platform: Social platform (twitter/instagram/facebook/linkedin/general)
        user_type: User tier (free/pro/enterprise)
        context: Additional context for processing
        user_id: ID of the user/brand making the request
        
    Returns:
        {
            "reply": "response_text",
            "action": "backend_action",
            "priority": "low/medium/high",
            "metadata": {
                "detected_intent": "pricing/support/etc",
                "confidence_score": 0.95,
                "suggested_followup": "additional_help_topic",
                "source": "custom/ai"
            }
        }
    """
    if context is None:
        context = {}
    
    # 1. Preprocess the message
    processed_message = preprocess_text(message)
    
    # 2. Detect intent from the message
    intent, confidence = detect_intent(processed_message)
    
    # 3. Check for custom reply in database
    custom_response = await check_custom_reply(processed_message, platform, user_id, intent)
    
    if custom_response:
        # 4a. If custom reply found, return it
        return {
            "reply": custom_response["reply"],
            "action": custom_response.get("action", "default_action"),
            "priority": custom_response.get("priority", "medium"),
            "metadata": {
                "detected_intent": intent,
                "confidence_score": confidence,
                "user_tier": user_type,
                "platform": platform,
                "timestamp": datetime.now().isoformat(),
                "source": "custom"
            }
        }
    else:
        # 4b. If no custom reply, use DeepSeek via OpenRouter
        ai_response = await get_deepseek_response(
            message=message,
            platform=platform,
            user_type=user_type,
            brand_id=user_id,
            context=context
        )
        
        return {
            "reply": ai_response["reply"],
            "action": ai_response.get("action", "default_action"),
            "priority": ai_response.get("priority", "medium"),
            "metadata": {
                "detected_intent": intent,
                "confidence_score": confidence,
                "user_tier": user_type,
                "platform": platform,
                "timestamp": datetime.now().isoformat(),
                "source": "ai",
                "model": settings.OPENROUTER_MODEL
            }
        }

# Helper functions
def preprocess_text(text: str) -> str:
    """Clean and normalize input text"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text

def detect_intent(message: str) -> tuple:
    """Enhanced intent detection with NLP"""
    # Simple keyword-based intent detection
    # In a production environment, this would use a more sophisticated ML model
    intents = {
        "pricing": ["price", "cost", "pricing", "how much", "rate", "fee", "plan", "subscription"],
        "support": ["help", "support", "issue", "problem", "error", "not working", "broken"],
        "onboarding": ["start", "begin", "tutorial", "guide", "how to", "setup", "getting started"],
        "feature": ["can it", "feature", "function", "capability", "able to", "does it"],
        "feedback": ["feedback", "suggest", "improve", "better", "opinion"],
    }
    
    # Check each intent's keywords
    for intent, keywords in intents.items():
        for keyword in keywords:
            if keyword in message:
                return (intent, 0.85)  # Simple confidence score
    
    # Default if no intent is detected
    return ("general", 0.5)

async def check_custom_reply(message: str, platform: str, brand_id: str, intent: str) -> Optional[Dict[str, Any]]:
    """Check if there's a custom reply for this message in the database"""
    if not brand_id:
        return None
    
    try:
        db = get_db_session()
        
        # First try to match by intent and brand_id
        custom_replies = db.query(CustomReply).filter(
            CustomReply.brand_id == brand_id,
            CustomReply.intent == intent,
            CustomReply.platform.in_([platform, "general"])
        ).all()
        
        if not custom_replies:
            # If no match by intent, try to match by keyword
            all_replies = db.query(CustomReply).filter(
                CustomReply.brand_id == brand_id,
                CustomReply.platform.in_([platform, "general"])
            ).all()
            
            # Check if any keywords match the message
            for reply in all_replies:
                if reply.keyword.lower() in message.lower():
                    custom_replies = [reply]
                    break
        
        if custom_replies:
            # Use the first matching reply
            reply = custom_replies[0]
            return {
                "reply": reply.custom_reply,
                "action": "custom_reply_action",
                "priority": "high"
            }
        
        return None
    except Exception as e:
        logger.error(f"Error checking custom replies: {str(e)}")
        return None
    finally:
        db.close()

async def get_deepseek_response(message: str, platform: str, user_type: str, 
                              brand_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get a response from DeepSeek via OpenRouter API with robust fallback logic"""
    if context is None:
        context = {}
    
    # Define fallback responses based on intent detection
    fallback_responses = {
        "pricing": {
            "reply": "Thank you for your interest in our pricing. Our plans start at $9.99/month for basic features, with premium plans offering additional capabilities. Please visit our pricing page for more details.",
            "action": "redirect_pricing_page",
            "priority": "high"
        },
        "support": {
            "reply": "I'm sorry to hear you're experiencing an issue. Our support team is available 24/7 to assist you. Please provide more details about your problem, and we'll help resolve it as soon as possible.",
            "action": "create_support_ticket",
            "priority": "high"
        },
        "onboarding": {
            "reply": "Welcome to Social Suit! Getting started is easy. First, connect your social accounts, then explore our dashboard to schedule posts, analyze performance, and engage with your audience. Check out our quick-start guide for more tips.",
            "action": "show_onboarding_guide",
            "priority": "medium"
        },
        "feature": {
            "reply": "Social Suit offers a wide range of features including post scheduling, analytics, audience engagement tools, and AI-powered content suggestions. Is there a specific feature you'd like to know more about?",
            "action": "show_features_page",
            "priority": "medium"
        },
        "feedback": {
            "reply": "Thank you for your feedback! We're constantly working to improve Social Suit based on user suggestions. Your input has been recorded and will be reviewed by our product team.",
            "action": "log_feedback",
            "priority": "medium"
        },
        "general": {
            "reply": "Thank you for reaching out to Social Suit. We're here to help you manage your social media presence more effectively. How can we assist you today?",
            "action": "general_assistance",
            "priority": "low"
        }
    }
    
    try:
        # Prepare the system prompt with context
        system_prompt = f"""
        You are an AI assistant for a social media management platform called Social Suit.
        
        CONTEXT:
        - Platform: {platform}
        - User tier: {user_type}
        - Brand ID: {brand_id if brand_id else 'Unknown'}
        
        Your task is to respond to user queries in a helpful, concise, and engaging way.
        Your response should be appropriate for the {platform} platform.
        
        RESPONSE FORMAT:
        You must respond in JSON format with the following structure:
        {{"reply": "your response text", "action": "suggested_action", "priority": "low/medium/high"}}
        
        Keep your responses concise and suitable for social media.
        """
        
        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://social-suit.com",  # Replace with your actual domain
            "X-Title": "Social Suit Auto-Engagement"
        }
        
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        # Make the API request with a shorter timeout to fail faster
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                settings.OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the response content
            ai_response = result["choices"][0]["message"]["content"]
            
            # Parse the JSON response
            try:
                parsed_response = json.loads(ai_response)
                return {
                    "reply": parsed_response.get("reply", "I'm not sure how to respond to that."),
                    "action": parsed_response.get("action", "default_action"),
                    "priority": parsed_response.get("priority", "medium")
                }
            except json.JSONDecodeError:
                # If the AI didn't return valid JSON, use the raw response
                return {
                    "reply": ai_response,
                    "action": "default_action",
                    "priority": "medium"
                }
    
    except httpx.TimeoutException as e:
        logger.warning(f"DeepSeek API timeout: {str(e)}")
        # Get the intent from the message to provide a relevant fallback
        intent, _ = detect_intent(message)
        return fallback_responses.get(intent, fallback_responses["general"])
        
    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek API HTTP error: {e.response.status_code} - {str(e)}")
        # Get the intent from the message to provide a relevant fallback
        intent, _ = detect_intent(message)
        return fallback_responses.get(intent, fallback_responses["general"])
        
    except Exception as e:
        logger.error(f"Error getting DeepSeek response: {str(e)}")
        # Get the intent from the message to provide a relevant fallback
        intent, _ = detect_intent(message)
        return fallback_responses.get(intent, fallback_responses["general"])