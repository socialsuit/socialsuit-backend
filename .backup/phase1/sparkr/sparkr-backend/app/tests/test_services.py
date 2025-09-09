import pytest
from unittest.mock import patch, MagicMock
from app.services.verification import (
    verify_twitter_task,
    verify_instagram_task,
    verify_facebook_task,
    verify_tiktok_task,
    verify_other_task,
    verify_submission
)
from app.services.points import calculate_points, award_points
from app.models.schemas import PlatformEnum


@pytest.fixture
def mock_submission():
    """Create a mock submission for testing"""
    submission = MagicMock()
    submission.id = "test-submission-id"
    submission.tweet_id = "1234567890"
    submission.ig_post_id = "instagram-post-123"
    submission.proof_url = "https://example.com/proof"
    submission.submission_url = "https://example.com/submission"
    submission.task = MagicMock()
    submission.task.points = 100
    return submission


@pytest.fixture
def mock_task():
    """Create a mock task for testing"""
    task = MagicMock()
    task.id = "test-task-id"
    task.platform = "twitter"
    task.points = 100
    return task


@pytest.mark.asyncio
async def test_verify_twitter_task(mock_submission):
    """Test Twitter task verification"""
    # Test with valid tweet_id
    result = await verify_twitter_task(mock_submission)
    assert result is True
    
    # Test with missing tweet_id
    mock_submission.tweet_id = None
    result = await verify_twitter_task(mock_submission)
    assert result is False


@pytest.mark.asyncio
async def test_verify_instagram_task(mock_submission):
    """Test Instagram task verification"""
    # Test with valid ig_post_id
    result = await verify_instagram_task(mock_submission)
    assert result is True
    
    # Test with missing ig_post_id
    mock_submission.ig_post_id = None
    result = await verify_instagram_task(mock_submission)
    assert result is False


@pytest.mark.asyncio
async def test_verify_facebook_task(mock_submission):
    """Test Facebook task verification"""
    # Test with valid proof_url
    result = await verify_facebook_task(mock_submission)
    assert result is True
    
    # Test with missing proof_url
    mock_submission.proof_url = None
    result = await verify_facebook_task(mock_submission)
    assert result is False


@pytest.mark.asyncio
async def test_verify_tiktok_task(mock_submission):
    """Test TikTok task verification"""
    # Test with valid proof_url
    mock_submission.proof_url = "https://example.com/proof"
    result = await verify_tiktok_task(mock_submission)
    assert result is True
    
    # Test with missing proof_url
    mock_submission.proof_url = None
    result = await verify_tiktok_task(mock_submission)
    assert result is False


@pytest.mark.asyncio
async def test_verify_other_task(mock_submission):
    """Test generic task verification"""
    # Test with valid submission_url
    result = await verify_other_task(mock_submission)
    assert result is True
    
    # Test with missing submission_url
    mock_submission.submission_url = None
    result = await verify_other_task(mock_submission)
    assert result is False


@pytest.mark.asyncio
async def test_verify_submission(mock_submission, mock_task):
    """Test submission verification based on platform"""
    # Test Twitter platform
    mock_task.platform = "twitter"
    mock_submission.tweet_id = "1234567890"
    result = await verify_submission(mock_submission, mock_task)
    assert result is True
    
    # Test Instagram platform
    mock_task.platform = "instagram"
    mock_submission.ig_post_id = "instagram-post-123"
    result = await verify_submission(mock_submission, mock_task)
    assert result is True
    
    # Test Facebook platform
    mock_task.platform = "facebook"
    mock_submission.proof_url = "https://example.com/proof"
    result = await verify_submission(mock_submission, mock_task)
    assert result is True
    
    # Test TikTok platform
    mock_task.platform = "tiktok"
    result = await verify_submission(mock_submission, mock_task)
    assert result is True
    
    # Test other platform
    mock_task.platform = "other"
    mock_submission.submission_url = "https://example.com/submission"
    result = await verify_submission(mock_submission, mock_task)
    assert result is True


def test_calculate_points(mock_submission):
    """Test points calculation"""
    # Test Twitter platform (10% bonus)
    points = calculate_points(PlatformEnum.TWITTER, mock_submission)
    assert points == 110  # 100 base points + 10% bonus
    
    # Test Instagram platform (15% bonus)
    points = calculate_points(PlatformEnum.INSTAGRAM, mock_submission)
    assert points == 115  # 100 base points + 15% bonus
    
    # Test Facebook platform (5% bonus)
    points = calculate_points(PlatformEnum.FACEBOOK, mock_submission)
    assert points == 105  # 100 base points + 5% bonus
    
    # Test TikTok platform (20% bonus)
    points = calculate_points(PlatformEnum.TIKTOK, mock_submission)
    assert points == 120  # 100 base points + 20% bonus


@pytest.mark.asyncio
async def test_award_points():
    """Test awarding points to a user"""
    # Mock session and execution results
    mock_session = MagicMock()
    mock_session.execute = MagicMock(return_value=MagicMock())
    mock_session.commit = MagicMock()
    
    # Test successful points award
    result = await award_points(
        user_id="test-user-id",
        submission_id="test-submission-id",
        points=100,
        session=mock_session
    )
    
    assert result is True
    assert mock_session.add.called
    assert mock_session.commit.called
    
    # Test exception handling
    mock_session.commit = MagicMock(side_effect=Exception("Test error"))
    result = await award_points(
        user_id="test-user-id",
        submission_id="test-submission-id",
        points=100,
        session=mock_session
    )
    
    assert result is False
    assert mock_session.rollback.called