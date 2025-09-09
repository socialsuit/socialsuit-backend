import pytest
from httpx import AsyncClient
from sqlmodel import select
from datetime import date

from sparkr.app.models.models import Campaign, Task, User, Submission
from sparkr.app.core.security import get_password_hash, create_access_token


@pytest.fixture
async def test_user(test_db_session):
    """Create a test user for submission tests"""
    user_id = None
    async with test_db_session() as session:
        # Check if test user already exists
        result = await session.execute(select(User).where(User.email == "testuser@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create test user
            user = User(
                email="testuser@example.com",
                username="testuser",
                hashed_password=get_password_hash("testpassword")
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        user_id = user.id
    
    # Create access token for the user
    access_token = create_access_token(data={"sub": user.email, "user_id": user_id})
    
    return {"id": user_id, "token": access_token}


@pytest.fixture
async def test_task(test_db_session):
    """Create a test campaign and task for submission tests"""
    task_id = None
    async with test_db_session() as session:
        # Create campaign
        campaign = Campaign(
            name="Test Campaign for Submissions",
            description="Campaign for testing submission endpoints",
            start_date=date.today(),
            end_date=date.today().replace(year=date.today().year + 1),
            status="active"
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        
        # Create task
        task = Task(
            campaign_id=campaign.id,
            title="Test Task for Submissions",
            description="Task for testing submission endpoints",
            platform="twitter",
            points=30,
            status="active"
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        task_id = task.id
    
    return task_id


@pytest.mark.asyncio
async def test_submit_task(async_client: AsyncClient, test_db_session, test_user, test_task):
    # Test data
    submission_data = {
        "task_id": test_task,
        "submission_url": "https://twitter.com/user/status/123456789",
        "tweet_id": "123456789"
    }
    
    # Submit task
    response = await async_client.post(
        "/api/v1/submissions/", 
        json=submission_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["task_id"] == submission_data["task_id"]
    assert data["user_id"] == test_user["id"]
    assert data["submission_url"] == submission_data["submission_url"]
    assert data["tweet_id"] == submission_data["tweet_id"]
    assert data["status"] == "pending"
    assert "id" in data
    
    # Verify in database
    async with test_db_session() as session:
        result = await session.execute(select(Submission).where(Submission.id == data["id"]))
        db_submission = result.scalar_one_or_none()
        assert db_submission is not None
        assert db_submission.task_id == submission_data["task_id"]


@pytest.mark.asyncio
async def test_get_submissions(async_client: AsyncClient, test_db_session, test_user, test_task):
    # Create test submission in DB
    async with test_db_session() as session:
        # Check if submission already exists
        result = await session.execute(
            select(Submission).where(
                Submission.task_id == test_task,
                Submission.user_id == test_user["id"]
            )
        )
        existing_submission = result.scalar_one_or_none()
        
        if not existing_submission:
            submission = Submission(
                task_id=test_task,
                user_id=test_user["id"],
                submission_url="https://twitter.com/user/status/987654321",
                tweet_id="987654321",
                status="pending",
                points_awarded=0
            )
            session.add(submission)
            await session.commit()
    
    # Get submissions
    response = await async_client.get(
        "/api/v1/submissions/",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # All submissions should belong to the test user
    for item in data:
        assert item["user_id"] == test_user["id"]


@pytest.mark.asyncio
async def test_get_submissions_by_task(async_client: AsyncClient, test_db_session, test_user, test_task):
    # Get submissions filtered by task
    response = await async_client.get(
        f"/api/v1/submissions/?task_id={test_task}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All submissions should belong to the specified task and user
    for item in data:
        assert item["task_id"] == test_task
        assert item["user_id"] == test_user["id"]