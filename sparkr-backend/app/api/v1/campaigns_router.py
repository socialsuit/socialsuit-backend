from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.schemas import CampaignCreate, CampaignResponse
from app.models.models import Campaign
from app.db.session import get_session

router = APIRouter(
    prefix="/campaigns", 
    tags=["Campaigns"],
    description="Endpoints for managing social media campaigns and their configurations"
)


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(campaign: CampaignCreate, session: AsyncSession = Depends(get_session)):
    """Create a new campaign"""
    # Create new campaign from the request data
    db_campaign = Campaign(
        name=campaign.name,
        description=campaign.description,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        status="active"
    )
    
    # Add to database
    session.add(db_campaign)
    await session.commit()
    await session.refresh(db_campaign)
    
    return db_campaign


@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(session: AsyncSession = Depends(get_session)):
    """Get all campaigns"""
    # Query all campaigns
    result = await session.execute(select(Campaign))
    campaigns = result.scalars().all()
    
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str, session: AsyncSession = Depends(get_session)):
    """Get a specific campaign by ID"""
    # Query campaign by ID
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, campaign_data: CampaignCreate, session: AsyncSession = Depends(get_session)):
    """Update a campaign"""
    # Query campaign by ID
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    # Update campaign fields
    campaign.name = campaign_data.name
    campaign.description = campaign_data.description
    campaign.start_date = campaign_data.start_date
    campaign.end_date = campaign_data.end_date
    
    # Save to database
    await session.commit()
    await session.refresh(campaign)
    
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str, session: AsyncSession = Depends(get_session)):
    """Delete a campaign"""
    # Query campaign by ID
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID {campaign_id} not found"
        )
    
    # Delete from database
    await session.delete(campaign)
    await session.commit()
    
    return None