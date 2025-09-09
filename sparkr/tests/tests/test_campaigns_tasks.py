import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from sparkr.app.models.models import Campaign, Task
from sparkr.app.models.schemas import PlatformEnum, StatusEnum


@pytest.fixture
async def test_campaign(session: AsyncSession):
    """Create a test campaign for tests"""
    today = date.today()
    test_campaign = Campaign(
        name="Test Campaign",
        description="Test campaign description",
        start_date=today,
        end_date=today + timedelta(days=30),
        status=StatusEnum.ACTIVE
    )
    
    session.add(test_campaign)
    await session.commit()
    await session.refresh(test_campaign)
    
    yield test_campaign
    
    # Cleanup
    await session.delete(test_campaign)
    await session.commit()


@pytest.fixture
async def test_task(session: AsyncSession, test_campaign: Campaign):
    """Create a test task for tests"""
    test_task = Task(
        campaign_id=test_campaign.id,
        title="Test Task",
        description="Test task description",
        platform=PlatformEnum.TWITTER,
        points=100,
        status=StatusEnum.ACTIVE
    )
    
    session.add(test_task)
    await session.commit()
    await session.refresh(test_task)
    
    yield test_task
    
    # Cleanup
    await session.delete(test_task)
    await session.commit()


# Campaign Tests
@pytest.mark.asyncio
async def test_create_campaign(async_client: AsyncClient):
    """Test creating a campaign"""
    today = date.today()
    response = await async_client.post(
        "/api/v1/campaigns/",
        json={
            "name": "New Campaign",
            "description": "New campaign description",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat()
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Campaign"
    assert data["description"] == "New campaign description"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_campaigns(async_client: AsyncClient, test_campaign: Campaign):
    """Test getting all campaigns"""
    response = await async_client.get("/api/v1/campaigns/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(campaign["id"] == test_campaign.id for campaign in data)


@pytest.mark.asyncio
async def test_get_campaign(async_client: AsyncClient, test_campaign: Campaign):
    """Test getting a specific campaign"""
    response = await async_client.get(f"/api/v1/campaigns/{test_campaign.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_campaign.id
    assert data["name"] == test_campaign.name


@pytest.mark.asyncio
async def test_update_campaign(async_client: AsyncClient, test_campaign: Campaign):
    """Test updating a campaign"""
    today = date.today()
    response = await async_client.put(
        f"/api/v1/campaigns/{test_campaign.id}",
        json={
            "name": "Updated Campaign",
            "description": "Updated description",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=60)).isoformat()
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_campaign.id
    assert data["name"] == "Updated Campaign"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_campaign(async_client: AsyncClient, session: AsyncSession):
    """Test deleting a campaign"""
    # Create a campaign to delete
    today = date.today()
    temp_campaign = Campaign(
        name="Temp Campaign",
        description="Temporary campaign to delete",
        start_date=today,
        end_date=today + timedelta(days=30),
        status=StatusEnum.ACTIVE
    )
    
    session.add(temp_campaign)
    await session.commit()
    await session.refresh(temp_campaign)
    
    # Delete the campaign
    response = await async_client.delete(f"/api/v1/campaigns/{temp_campaign.id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    response = await async_client.get(f"/api/v1/campaigns/{temp_campaign.id}")
    assert response.status_code == 404


# Task Tests
@pytest.mark.asyncio
async def test_create_task(async_client: AsyncClient, test_campaign: Campaign):
    """Test creating a task"""
    response = await async_client.post(
        "/api/v1/tasks/",
        json={
            "campaign_id": test_campaign.id,
            "title": "New Task",
            "description": "New task description",
            "platform": "twitter",
            "points": 150
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["campaign_id"] == test_campaign.id
    assert data["points"] == 150
    assert "id" in data


@pytest.mark.asyncio
async def test_get_tasks(async_client: AsyncClient, test_task: Task):
    """Test getting all tasks"""
    response = await async_client.get("/api/v1/tasks/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(task["id"] == test_task.id for task in data)


@pytest.mark.asyncio
async def test_get_tasks_by_campaign(async_client: AsyncClient, test_task: Task, test_campaign: Campaign):
    """Test getting tasks filtered by campaign"""
    response = await async_client.get(f"/api/v1/tasks/?campaign_id={test_campaign.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(task["campaign_id"] == test_campaign.id for task in data)
    assert any(task["id"] == test_task.id for task in data)


@pytest.mark.asyncio
async def test_get_task(async_client: AsyncClient, test_task: Task):
    """Test getting a specific task"""
    response = await async_client.get(f"/api/v1/tasks/{test_task.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_task.id
    assert data["title"] == test_task.title


@pytest.mark.asyncio
async def test_update_task(async_client: AsyncClient, test_task: Task, test_campaign: Campaign):
    """Test updating a task"""
    response = await async_client.put(
        f"/api/v1/tasks/{test_task.id}",
        json={
            "campaign_id": test_campaign.id,
            "title": "Updated Task",
            "description": "Updated task description",
            "platform": "instagram",
            "points": 200
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_task.id
    assert data["title"] == "Updated Task"
    assert data["platform"] == "instagram"
    assert data["points"] == 200


@pytest.mark.asyncio
async def test_delete_task(async_client: AsyncClient, session: AsyncSession, test_campaign: Campaign):
    """Test deleting a task"""
    # Create a task to delete
    temp_task = Task(
        campaign_id=test_campaign.id,
        title="Temp Task",
        description="Temporary task to delete",
        platform=PlatformEnum.TWITTER,
        points=100,
        status=StatusEnum.ACTIVE
    )
    
    session.add(temp_task)
    await session.commit()
    await session.refresh(temp_task)
    
    # Delete the task
    response = await async_client.delete(f"/api/v1/tasks/{temp_task.id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    response = await async_client.get(f"/api/v1/tasks/{temp_task.id}")
    assert response.status_code == 404