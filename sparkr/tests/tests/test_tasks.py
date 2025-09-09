import pytest
from httpx import AsyncClient
from sqlmodel import select
from datetime import date

from sparkr.app.models.models import Campaign, Task


@pytest.fixture
async def test_campaign(test_db_session):
    """Create a test campaign for task tests"""
    campaign_id = None
    async with test_db_session() as session:
        campaign = Campaign(
            name="Test Campaign for Tasks",
            description="Campaign for testing task endpoints",
            start_date=date.today(),
            end_date=date.today().replace(year=date.today().year + 1),
            status="active"
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        campaign_id = campaign.id
    
    return campaign_id


@pytest.mark.asyncio
async def test_create_task(async_client: AsyncClient, test_db_session, test_campaign):
    # Test data
    task_data = {
        "campaign_id": test_campaign,
        "title": "Test Task",
        "description": "A test task",
        "platform": "twitter",
        "points": 10
    }
    
    # Create task
    response = await async_client.post("/api/v1/tasks/", json=task_data)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["campaign_id"] == task_data["campaign_id"]
    assert data["platform"] == task_data["platform"]
    assert data["points"] == task_data["points"]
    assert "id" in data
    
    # Verify in database
    async with test_db_session() as session:
        result = await session.execute(select(Task).where(Task.id == data["id"]))
        db_task = result.scalar_one_or_none()
        assert db_task is not None
        assert db_task.title == task_data["title"]


@pytest.mark.asyncio
async def test_get_tasks(async_client: AsyncClient, test_db_session, test_campaign):
    # Create test task in DB
    async with test_db_session() as session:
        task = Task(
            campaign_id=test_campaign,
            title="Test Task List",
            description="Task for testing list endpoint",
            platform="twitter",
            points=15,
            status="active"
        )
        session.add(task)
        await session.commit()
    
    # Get tasks
    response = await async_client.get("/api/v1/tasks/")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Find our test task
    found = False
    for item in data:
        if item["title"] == "Test Task List":
            found = True
            break
    
    assert found, "Test task not found in response"


@pytest.mark.asyncio
async def test_get_tasks_by_campaign(async_client: AsyncClient, test_db_session, test_campaign):
    # Create test task in DB
    async with test_db_session() as session:
        task = Task(
            campaign_id=test_campaign,
            title="Test Task for Campaign Filter",
            description="Task for testing campaign filter",
            platform="instagram",
            points=20,
            status="active"
        )
        session.add(task)
        await session.commit()
    
    # Get tasks filtered by campaign
    response = await async_client.get(f"/api/v1/tasks/?campaign_id={test_campaign}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # All tasks should belong to the specified campaign
    for item in data:
        assert item["campaign_id"] == test_campaign


@pytest.mark.asyncio
async def test_get_task(async_client: AsyncClient, test_db_session, test_campaign):
    # Create test task in DB
    task_id = None
    async with test_db_session() as session:
        task = Task(
            campaign_id=test_campaign,
            title="Test Task Detail",
            description="Task for testing detail endpoint",
            platform="facebook",
            points=25,
            status="active"
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        task_id = task.id
    
    # Get task by ID
    response = await async_client.get(f"/api/v1/tasks/{task_id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test Task Detail"


@pytest.mark.asyncio
async def test_get_nonexistent_task(async_client: AsyncClient):
    # Get non-existent task
    response = await async_client.get("/api/v1/tasks/nonexistent-id")
    
    # Check response
    assert response.status_code == 404