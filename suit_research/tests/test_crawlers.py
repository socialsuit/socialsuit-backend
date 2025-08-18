import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, List, Any
import aiohttp
from bs4 import BeautifulSoup

from app.services.crawler import WebCrawler, FundingNewsCrawler, ProjectCrawler
from app.models.project import Project


class TestWebCrawler:
    """Test cases for base web crawler functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session for testing."""
        session = Mock(spec=aiohttp.ClientSession)
        return session
    
    @pytest.fixture
    def web_crawler(self, mock_session):
        """Create web crawler instance with mocked session."""
        return WebCrawler(session=mock_session)
    
    @pytest.mark.asyncio
    async def test_fetch_page_success(self, web_crawler, mock_session):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        content = await web_crawler.fetch_page("https://example.com")
        
        assert "Test content" in content
        mock_session.get.assert_called_once_with(
            "https://example.com",
            headers=web_crawler.default_headers,
            timeout=web_crawler.timeout
        )
    
    @pytest.mark.asyncio
    async def test_fetch_page_404_error(self, web_crawler, mock_session):
        """Test handling of 404 errors."""
        mock_response = Mock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Not Found")
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(aiohttp.ClientResponseError):
            await web_crawler.fetch_page("https://example.com/notfound")
    
    @pytest.mark.asyncio
    async def test_fetch_page_timeout(self, web_crawler, mock_session):
        """Test handling of request timeouts."""
        mock_session.get.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(asyncio.TimeoutError):
            await web_crawler.fetch_page("https://slow-site.com")
    
    @pytest.mark.asyncio
    async def test_fetch_page_with_retries(self, web_crawler, mock_session):
        """Test retry mechanism for failed requests."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status = 500
        
        mock_response_success = Mock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="Success")
        
        mock_session.get.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success
        ]
        
        content = await web_crawler.fetch_page_with_retry("https://example.com", max_retries=2)
        
        assert content == "Success"
        assert mock_session.get.call_count == 2
    
    def test_parse_html_content(self, web_crawler):
        """Test HTML parsing functionality."""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p class="description">Test description</p>
                <a href="https://example.com">Link</a>
            </body>
        </html>
        """
        
        soup = web_crawler.parse_html(html)
        
        assert soup.title.string == "Test Page"
        assert soup.h1.string == "Main Title"
        assert soup.find('p', class_='description').string == "Test description"
    
    def test_extract_links(self, web_crawler):
        """Test link extraction from HTML."""
        html = """
        <html><body>
            <a href="https://example.com">External Link</a>
            <a href="/internal">Internal Link</a>
            <a href="mailto:test@example.com">Email</a>
            <a href="#anchor">Anchor</a>
        </body></html>
        """
        
        links = web_crawler.extract_links(html, base_url="https://test.com")
        
        assert "https://example.com" in links
        assert "https://test.com/internal" in links
        assert "mailto:test@example.com" not in links  # Should filter out non-http links
    
    def test_extract_text_content(self, web_crawler):
        """Test clean text extraction from HTML."""
        html = """
        <html><body>
            <h1>Title</h1>
            <p>Paragraph 1</p>
            <script>console.log('script');</script>
            <style>body { color: red; }</style>
            <p>Paragraph 2</p>
        </body></html>
        """
        
        text = web_crawler.extract_text(html)
        
        assert "Title" in text
        assert "Paragraph 1" in text
        assert "Paragraph 2" in text
        assert "console.log" not in text  # Scripts should be removed
        assert "color: red" not in text  # Styles should be removed


class TestFundingNewsCrawler:
    """Test cases for funding news crawler."""
    
    @pytest.fixture
    def funding_crawler(self):
        """Create funding news crawler instance."""
        return FundingNewsCrawler()
    
    @pytest.mark.asyncio
    async def test_crawl_techcrunch_funding(self, funding_crawler):
        """Test crawling TechCrunch funding articles."""
        sample_html = """
        <article>
            <h1>DeFi Startup Raises $50M Series B</h1>
            <div class="article-content">
                <p>DeFi Protocol, a decentralized finance platform, announced today 
                   that it has raised $50 million in Series B funding led by 
                   Andreessen Horowitz, with participation from Coinbase Ventures.</p>
                <p>The company plans to use the funding to expand its lending products.</p>
            </div>
            <time datetime="2024-01-15T10:00:00Z">January 15, 2024</time>
        </article>
        """
        
        with patch.object(funding_crawler, 'fetch_page', return_value=sample_html):
            funding_data = await funding_crawler.parse_techcrunch_article(
                "https://techcrunch.com/2024/01/15/defi-startup-raises-50m"
            )
            
            assert funding_data["project_name"] == "DeFi Protocol"
            assert "$50 million" in funding_data["amount"]
            assert funding_data["round_type"] == "Series B"
            assert "Andreessen Horowitz" in funding_data["investors"]
            assert "Coinbase Ventures" in funding_data["investors"]
    
    @pytest.mark.asyncio
    async def test_crawl_coindesk_funding(self, funding_crawler):
        """Test crawling CoinDesk funding articles."""
        sample_html = """
        <div class="article-wrap">
            <h1>NFT Marketplace Secures $25M in Seed Funding</h1>
            <div class="entry-content">
                <p>NFT Exchange, a new marketplace for digital collectibles, 
                   has secured $25 million in seed funding from Binance Labs 
                   and other investors.</p>
            </div>
            <time>2024-01-10</time>
        </div>
        """
        
        with patch.object(funding_crawler, 'fetch_page', return_value=sample_html):
            funding_data = await funding_crawler.parse_coindesk_article(
                "https://coindesk.com/business/2024/01/10/nft-marketplace-funding"
            )
            
            assert funding_data["project_name"] == "NFT Exchange"
            assert "$25 million" in funding_data["amount"]
            assert funding_data["round_type"] == "Seed"
            assert "Binance Labs" in funding_data["investors"]
    
    def test_extract_funding_amount(self, funding_crawler):
        """Test extraction of funding amounts from text."""
        test_cases = [
            ("raised $10 million in Series A", "$10 million"),
            ("secured €5.5M in funding", "€5.5M"),
            ("$2.3B investment round", "$2.3B"),
            ("undisclosed amount", "undisclosed"),
            ("no funding mentioned", None)
        ]
        
        for text, expected in test_cases:
            result = funding_crawler.extract_amount(text)
            assert result == expected
    
    def test_extract_round_type(self, funding_crawler):
        """Test extraction of funding round types."""
        test_cases = [
            ("Series A funding round", "Series A"),
            ("seed investment", "Seed"),
            ("pre-seed round", "Pre-Seed"),
            ("Series B extension", "Series B"),
            ("strategic investment", "Strategic"),
            ("ICO token sale", "ICO")
        ]
        
        for text, expected in test_cases:
            result = funding_crawler.extract_round_type(text)
            assert result == expected
    
    def test_extract_investors(self, funding_crawler):
        """Test extraction of investor names from article text."""
        text = """
        The round was led by Andreessen Horowitz (a16z) with participation 
        from Coinbase Ventures, Binance Labs, and Pantera Capital. 
        Other investors include Sequoia Capital and Union Square Ventures.
        """
        
        investors = funding_crawler.extract_investors(text)
        
        expected_investors = [
            "Andreessen Horowitz", "Coinbase Ventures", "Binance Labs",
            "Pantera Capital", "Sequoia Capital", "Union Square Ventures"
        ]
        
        for investor in expected_investors:
            assert investor in investors


class TestProjectCrawler:
    """Test cases for project information crawler."""
    
    @pytest.fixture
    def project_crawler(self):
        """Create project crawler instance."""
        return ProjectCrawler()
    
    @pytest.mark.asyncio
    async def test_crawl_project_website(self, project_crawler):
        """Test crawling project website for information."""
        sample_html = """
        <html>
            <head>
                <title>DeFi Protocol - Decentralized Finance Platform</title>
                <meta name="description" content="A leading DeFi protocol for lending and borrowing">
            </head>
            <body>
                <h1>DeFi Protocol</h1>
                <p>Our mission is to democratize finance through blockchain technology.</p>
                <div class="team">
                    <h2>Team</h2>
                    <div class="member">John Doe - CEO</div>
                    <div class="member">Jane Smith - CTO</div>
                </div>
                <footer>
                    <a href="https://twitter.com/defiprotocol">Twitter</a>
                    <a href="https://github.com/defiprotocol">GitHub</a>
                </footer>
            </body>
        </html>
        """
        
        with patch.object(project_crawler, 'fetch_page', return_value=sample_html):
            project_data = await project_crawler.crawl_project_info("https://defiprotocol.com")
            
            assert project_data["name"] == "DeFi Protocol"
            assert "lending and borrowing" in project_data["description"]
            assert "https://twitter.com/defiprotocol" in project_data["social_links"]
            assert "https://github.com/defiprotocol" in project_data["social_links"]
    
    @pytest.mark.asyncio
    async def test_extract_social_links(self, project_crawler):
        """Test extraction of social media links."""
        html = """
        <div class="social">
            <a href="https://twitter.com/project">Twitter</a>
            <a href="https://t.me/projectchat">Telegram</a>
            <a href="https://discord.gg/project">Discord</a>
            <a href="https://medium.com/@project">Medium</a>
            <a href="https://github.com/project/repo">GitHub</a>
            <a href="https://example.com">Website</a>
        </div>
        """
        
        social_links = project_crawler.extract_social_links(html)
        
        assert "https://twitter.com/project" in social_links
        assert "https://t.me/projectchat" in social_links
        assert "https://discord.gg/project" in social_links
        assert "https://medium.com/@project" in social_links
        assert "https://github.com/project/repo" in social_links
        assert "https://example.com" not in social_links  # Should filter non-social links
    
    def test_extract_team_info(self, project_crawler):
        """Test extraction of team member information."""
        html = """
        <div class="team">
            <div class="member">
                <h3>John Doe</h3>
                <p>CEO & Founder</p>
                <p>Former Goldman Sachs, Stanford MBA</p>
            </div>
            <div class="member">
                <h3>Jane Smith</h3>
                <p>CTO</p>
                <p>Ex-Google, MIT Computer Science</p>
            </div>
        </div>
        """
        
        team_info = project_crawler.extract_team_info(html)
        
        assert len(team_info) == 2
        assert team_info[0]["name"] == "John Doe"
        assert team_info[0]["role"] == "CEO & Founder"
        assert "Goldman Sachs" in team_info[0]["background"]
    
    @pytest.mark.asyncio
    async def test_crawl_github_stats(self, project_crawler):
        """Test crawling GitHub repository statistics."""
        github_api_response = {
            "name": "defi-protocol",
            "description": "Decentralized finance protocol",
            "stargazers_count": 1250,
            "forks_count": 340,
            "open_issues_count": 25,
            "language": "Solidity",
            "created_at": "2023-01-15T10:00:00Z",
            "updated_at": "2024-01-15T15:30:00Z"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value=github_api_response)
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            github_stats = await project_crawler.crawl_github_stats("defiprotocol/defi-protocol")
            
            assert github_stats["stars"] == 1250
            assert github_stats["forks"] == 340
            assert github_stats["issues"] == 25
            assert github_stats["language"] == "Solidity"
    
    def test_detect_project_category(self, project_crawler):
        """Test automatic project category detection."""
        test_cases = [
            ("DeFi lending protocol", "DEFI"),
            ("Layer 2 scaling solution", "LAYER_2"),
            ("NFT marketplace platform", "NFT"),
            ("Blockchain gaming platform", "GAMING"),
            ("Cryptocurrency wallet", "WALLET"),
            ("Decentralized exchange", "DEX")
        ]
        
        for description, expected_category in test_cases:
            category = project_crawler.detect_category(description)
            assert category == expected_category