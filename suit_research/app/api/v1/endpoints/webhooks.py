"""Webhook-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import json
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.auth_middleware import get_api_key
from app.api.schemas.project import WebhookPayload, WebhookResponse

router = APIRouter()
logger = logging.getLogger(__name__)


async def process_webhook_data(payload: Dict[str, Any], source: str, db: AsyncSession):
    """
    Background task to process webhook data.
    
    This function can be extended to handle different webhook sources
    and process the data accordingly (e.g., create projects, funding rounds, etc.)
    """
    try:
        logger.info(f"Processing webhook from {source}: {json.dumps(payload, default=str)}")
        
        # Example processing logic - can be extended based on webhook source
        if source == "crunchbase":
            # Process Crunchbase webhook data
            await process_crunchbase_webhook(payload, db)
        elif source == "pitchbook":
            # Process PitchBook webhook data
            await process_pitchbook_webhook(payload, db)
        elif source == "custom":
            # Process custom webhook data
            await process_custom_webhook(payload, db)
        else:
            logger.warning(f"Unknown webhook source: {source}")
        
        logger.info(f"Successfully processed webhook from {source}")
        
    except Exception as e:
        logger.error(f"Error processing webhook from {source}: {str(e)}")
        raise


async def process_crunchbase_webhook(payload: Dict[str, Any], db: AsyncSession):
    """
    Process Crunchbase webhook data.
    
    Example implementation - should be customized based on actual Crunchbase webhook format.
    """
    # Example: Extract company and funding information
    if "organization" in payload:
        org_data = payload["organization"]
        logger.info(f"Processing Crunchbase organization: {org_data.get('name', 'Unknown')}")
    
    if "funding_round" in payload:
        funding_data = payload["funding_round"]
        logger.info(f"Processing Crunchbase funding round: {funding_data.get('funding_type', 'Unknown')}")


async def process_pitchbook_webhook(payload: Dict[str, Any], db: AsyncSession):
    """
    Process PitchBook webhook data.
    
    Example implementation - should be customized based on actual PitchBook webhook format.
    """
    # Example: Extract deal information
    if "deal" in payload:
        deal_data = payload["deal"]
        logger.info(f"Processing PitchBook deal: {deal_data.get('deal_type', 'Unknown')}")


async def process_custom_webhook(payload: Dict[str, Any], db: AsyncSession):
    """
    Process custom webhook data.
    
    This can be used for internal systems or custom integrations.
    """
    # Example: Process custom data format
    if "event_type" in payload:
        event_type = payload["event_type"]
        logger.info(f"Processing custom webhook event: {event_type}")


@router.post("/", response_model=WebhookResponse, status_code=202)
async def receive_webhook(
    webhook_data: WebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Receive and process webhook data.
    
    This endpoint accepts webhook payloads from various sources and processes them
    in the background. The webhook data is validated and then queued for processing.
    
    Requires API key authentication.
    
    - **source**: The source of the webhook (e.g., 'crunchbase', 'pitchbook', 'custom')
    - **event_type**: The type of event (e.g., 'funding_round', 'company_update')
    - **data**: The webhook payload data
    - **timestamp**: When the event occurred (optional, defaults to current time)
    """
    try:
        # Log webhook receipt
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"Received webhook from {webhook_data.source} "
            f"(event: {webhook_data.event_type}, IP: {client_ip})"
        )
        
        # Validate webhook data
        if not webhook_data.data:
            raise HTTPException(status_code=400, detail="Webhook data cannot be empty")
        
        # Set timestamp if not provided
        if not webhook_data.timestamp:
            webhook_data.timestamp = datetime.utcnow()
        
        # Queue webhook processing as background task
        background_tasks.add_task(
            process_webhook_data,
            webhook_data.data,
            webhook_data.source,
            db
        )
        
        # Return immediate response
        return WebhookResponse(
            status="accepted",
            message=f"Webhook from {webhook_data.source} accepted for processing",
            webhook_id=f"{webhook_data.source}_{int(webhook_data.timestamp.timestamp())}",
            received_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error processing webhook")


@router.post("/test", response_model=WebhookResponse, status_code=200)
async def test_webhook(
    webhook_data: WebhookPayload,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Test webhook endpoint for development and debugging.
    
    This endpoint processes webhook data synchronously and returns the result immediately.
    Useful for testing webhook integrations during development.
    
    Requires API key authentication.
    """
    try:
        logger.info(f"Testing webhook from {webhook_data.source} (event: {webhook_data.event_type})")
        
        # Validate webhook data
        if not webhook_data.data:
            raise HTTPException(status_code=400, detail="Webhook data cannot be empty")
        
        # Set timestamp if not provided
        if not webhook_data.timestamp:
            webhook_data.timestamp = datetime.utcnow()
        
        # Process webhook data synchronously for testing
        await process_webhook_data(
            webhook_data.data,
            webhook_data.source,
            db
        )
        
        return WebhookResponse(
            status="processed",
            message=f"Test webhook from {webhook_data.source} processed successfully",
            webhook_id=f"test_{webhook_data.source}_{int(webhook_data.timestamp.timestamp())}",
            received_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing test webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing test webhook: {str(e)}")