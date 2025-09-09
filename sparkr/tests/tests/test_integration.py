import pytest
from unittest.mock import patch
from datetime import datetime, timedelta



# Mock for the verification service
class MockVerifier:
    def __init__(self, *args, **kwargs):
        pass
        
    async def verify(self, *args, **kwargs):
        return True, "Verification successful"


@pytest.fixture
async def registered_user(async_client):
    """Register a test user and return the user data with auth token"""
    # Use the client directly - it's already yielded by the fixture
    
    # Register user
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration_test@example.com",
            "username": "integration_tester",
            "password": "securepassword123"
        }
    )
    
    assert register_response.status_code == 201
    user_data = register_response.json()
    
    # Login to get token
    login_response = await async_client.post(
        "/api/v1/auth/token",
        data={
            "username": "integration_test@example.com",
            "password": "securepassword123"
        }
    )
    
    assert login_response.status_code == 200
    token_data = login_response.json()
    
    return {
        "user": user_data,
        "token": token_data["access_token"]
    }


@pytest.mark.asyncio
async def test_complete_user_flow(async_client, registered_user, monkeypatch):
    """Test the complete user flow from registration to leaderboard"""
    # Await the registered_user fixture to get the actual user data
    user_data = await registered_user
    
    # Setup auth header with the token from the awaited user data
    headers = {"Authorization": f"Bearer {user_data['token']}"}
    
    # 1. Create a campaign
    campaign_data = {
        "name": "Integration Test Campaign",
        "description": "Campaign created during integration testing",
        "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    
    campaign_response = await async_client.post(
        "/api/v1/campaigns/",
        json=campaign_data,
        headers=headers
    )
    
    assert campaign_response.status_code == 201
    campaign = campaign_response.json()
    assert campaign["name"] == campaign_data["name"]
    
    # 2. Create a task in the campaign
    task_data = {
        "campaign_id": campaign["id"],
        "title": "Integration Test Task",
        "description": "Task created during integration testing",
        "platform": "TWITTER",
        "points": 100
    }
    
    task_response = await async_client.post(
        "/api/v1/tasks/",
        json=task_data,
        headers=headers
    )
    
    assert task_response.status_code == 201
    task = task_response.json()
    assert task["title"] == task_data["title"]
    assert task["points"] == task_data["points"]
    
    # 3. Submit the task
    submission_data = {
        "submission_url": "https://twitter.com/example/status/123456789",
        "tweet_id": "123456789"
    }
    
    # Mock the verification service
    with patch('app.services.verification.TwitterVerifier', MockVerifier):
        with patch('app.services.verification.InstagramVerifier', MockVerifier):
            submission_response = await async_client.post(
                f"/api/v1/submissions/tasks/{task['id']}/submit",
                json=submission_data,
                headers=headers
            )
    
    assert submission_response.status_code == 201
    submission = submission_response.json()
    assert submission["task_id"] == task["id"]
    assert submission["user_id"] == registered_user["user"]["id"]
    
    # 4. Mock worker auto-verification
    # This would normally be done by a Celery worker, but we'll mock it
    with patch('app.services.verification.verify_submission', return_value=(True, "Verified")):
        # Get the submission by ID
        submission_id = submission["id"]
        
        # Update submission status directly (mocking worker verification)
        update_response = await async_client.patch(
            f"/api/v1/submissions/{submission_id}",
            json={
                "verification_status": "VERIFIED",
                "points_awarded": task["points"]
            },
            headers=headers
        )
        
        assert update_response.status_code == 200
        updated_submission = update_response.json()
        assert updated_submission["verification_status"] == "VERIFIED"
        assert updated_submission["points_awarded"] == task["points"]
    
    # 5. Check user points
    user_response = await async_client.get(
        "/api/v1/auth/me",
        headers=headers
    )
    
    assert user_response.status_code == 200
    user_data = user_response.json()
    assert user_data["total_points"] >= task["points"]
    
    # 6. Check leaderboard
    leaderboard_response = await async_client.get(
        "/api/v1/leaderboard/",
        headers=headers
    )
    
    assert leaderboard_response.status_code == 200
    leaderboard = leaderboard_response.json()
    assert len(leaderboard) > 0
    
    # Check campaign-specific leaderboard
    campaign_leaderboard_response = await async_client.get(
        f"/api/v1/leaderboard/campaign/{campaign['id']}",
        headers=headers
    )
    
    assert campaign_leaderboard_response.status_code == 200
    campaign_leaderboard = campaign_leaderboard_response.json()
    assert len(campaign_leaderboard) > 0