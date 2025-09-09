import pytest
from unittest.mock import patch, MagicMock
from app.services.verification import TwitterVerifier


@pytest.fixture
def twitter_verifier():
    """Create a TwitterVerifier instance for testing"""
    return TwitterVerifier(bearer_token="test_token")


class TestTwitterVerifier:
    """Tests for the TwitterVerifier class"""
    
    def test_extract_tweet_id(self, twitter_verifier):
        """Test extracting tweet ID from URL"""
        # Test valid tweet URL
        tweet_url = "https://twitter.com/username/status/123456789"
        tweet_id = twitter_verifier.extract_tweet_id(tweet_url)
        assert tweet_id == "123456789"
        
        # Test invalid tweet URL
        tweet_url = "https://twitter.com/username/invalid/123456789"
        tweet_id = twitter_verifier.extract_tweet_id(tweet_url)
        assert tweet_id is None
        
        # Test empty URL
        tweet_id = twitter_verifier.extract_tweet_id("")
        assert tweet_id is None
    
    def test_extract_user_handle(self, twitter_verifier):
        """Test extracting and normalizing user handle"""
        # Test with @ symbol
        user = twitter_verifier.extract_user_handle("@username")
        assert user == "username"
        
        # Test without @ symbol
        user = twitter_verifier.extract_user_handle("username")
        assert user == "username"
        
        # Test with whitespace
        user = twitter_verifier.extract_user_handle(" @username ")
        assert user == "username"
    
    @pytest.mark.asyncio
    async def test_verify_like_success(self, twitter_verifier):
        """Test successful like verification"""
        # Test with mock pattern that should return True
        result = await twitter_verifier.verify_like("testuser", "https://twitter.com/username/status/123456789")
        assert result is True
        
        # Test with 'valid' in username
        result = await twitter_verifier.verify_like("valid_user", "https://twitter.com/username/status/987654321")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_like_failure(self, twitter_verifier):
        """Test failed like verification"""
        # Test with invalid user
        result = await twitter_verifier.verify_like("invalid_user", "https://twitter.com/username/status/123456789")
        assert result is False
        
        # Test with invalid tweet URL
        result = await twitter_verifier.verify_like("testuser", "https://twitter.com/username/invalid/123456789")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_retweet_success(self, twitter_verifier):
        """Test successful retweet verification"""
        # Test with mock pattern that should return True
        result = await twitter_verifier.verify_retweet("testuser", "https://twitter.com/username/status/123456789")
        assert result is True
        
        # Test with 'valid' in username
        result = await twitter_verifier.verify_retweet("valid_user", "https://twitter.com/username/status/987654321")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_retweet_failure(self, twitter_verifier):
        """Test failed retweet verification"""
        # Test with invalid user
        result = await twitter_verifier.verify_retweet("invalid_user", "https://twitter.com/username/status/123456789")
        assert result is False
        
        # Test with invalid tweet URL
        result = await twitter_verifier.verify_retweet("testuser", "https://twitter.com/username/invalid/123456789")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, twitter_verifier):
        """Test error handling during API calls"""
        # Test exception handling in verify_like
        with patch.object(TwitterVerifier, 'extract_tweet_id', side_effect=Exception("Test error")):
            result = await twitter_verifier.verify_like("testuser", "https://twitter.com/username/status/123456789")
            assert result is False
        
        # Test exception handling in verify_retweet
        with patch.object(TwitterVerifier, 'extract_tweet_id', side_effect=Exception("Test error")):
            result = await twitter_verifier.verify_retweet("testuser", "https://twitter.com/username/status/123456789")
            assert result is False