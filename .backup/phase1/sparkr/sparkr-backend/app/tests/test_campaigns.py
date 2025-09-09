import pytest
from httpx import AsyncClient
from sqlmodel import select
from datetime import date

from app.models.models import Campaign


@pytest.mark.asyncio
async def test_create_campaign(async_client: AsyncClient, test_db_session):
    # Test data
    campaign_data = {
        "name": "Test Campaign",
        "description": "A test campaign",
        "start_date": str(date.today()),
        "end_date": str(date.today().replace(year=date.today().year + 1)),
        "status": "active"
    }
    
    # Create campaign
    response = await async_client.post("/api/v1/campaigns/", json=campaign_data)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == campaign_data["name"]
    assert data["description"] == campaign_data["description"]
    assert "id" in data
    
    # Verify in database
    async with test_db_session() as session:
        result = await session.execute(select(Campaign).where(Campaign.id == data["id"]))
        db_campaign = result.scalar_one_or_none()
        assert db_campaign is not None
        assert db_campaign.name == campaign_data["name"]


@pytest.mark.asyncio
async def test_get_campaigns(async_client: AsyncClient, test_db_session):
    # Create test campaign in DB
    async with test_db_session() as session:
        campaign = Campaign(
            name="Test Campaign List",
            description="Campaign for testing list endpoint",
            start_date=date.today(),
            end_date=date.today().replace(year=date.today().year + 1),
            status="active"
        )
        session.add(campaign)
        await session.commit()
    
    # Get campaigns
    response = await async_client.get("/api/v1/campaigns/")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Find our test campaign
    found = False
    for item in data:
        if item["name"] == "Test Campaign List":
            found = True
            break
    
    assert found, "Test campaign not found in response"


@pytest.mark.asyncio
async def test_get_campaign(async_client: AsyncClient, test_db_session):
    # Create test campaign in DB
    campaign_id = None
    async with test_db_session() as session:
        campaign = Campaign(
            name="Test Campaign Detail",
            description="Campaign for testing detail endpoint",
            start_date=date.today(),
            end_date=date.today().replace(year=date.today().year + 1),
            status="active"
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        campaign_id = campaign.id
    
    # Get campaign by ID
    response = await async_client.get(f"/api/v1/campaigns/{campaign_id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == campaign_id
    assert data["name"] == "Test Campaign Detail"


@pytest.mark.asyncio
async def test_get_nonexistent_campaign(async_client: AsyncClient):
    # Get non-existent campaign
    response = await async_client.get("/api/v1/campaigns/nonexistent-id")
    
    # Check response
    assert response.status_code == 404