import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, List, Any

from app.services.funding_parser import FundingParser
from app.services.category_detector import ProjectCategoryDetector
from app.models.project import Project
from app.schemas.project import ProjectCreate


class TestFundingParser:
    """Test cases for funding parser service."""
    
    @pytest.fixture
    def funding_parser(self):
        """Create a funding parser instance for testing."""
        return FundingParser()
    
    @pytest.fixture
    def sample_funding_data(self):
        """Sample funding round data for testing."""
        return {
            "project_name": "DeFi Protocol",
            "description": "A decentralized finance protocol for lending",
            "amount": "10000000",
            "currency": "USD",
            "round_type": "Series A",
            "date": "2024-01-15",
            "investors": ["Venture Capital A", "Crypto Fund B"],
            "website": "https://defiprotocol.com",
            "token_symbol": "DFP"
        }
    
    def test_parse_funding_amount(self, funding_parser):
        """Test parsing of funding amounts in various formats."""
        test_cases = [
            ("$10M", 10000000),
            ("$5.5 million", 5500000),
            ("€2.3M", 2300000),
            ("1.2B", 1200000000),
            ("500K", 500000),
            ("undisclosed", None),
            ("", None)
        ]
        
        for amount_str, expected in test_cases:
            result = funding_parser.parse_amount(amount_str)
            assert result == expected
    
    def test_parse_funding_date(self, funding_parser):
        """Test parsing of funding dates in various formats."""
        test_cases = [
            ("2024-01-15", datetime(2024, 1, 15)),
            ("January 15, 2024", datetime(2024, 1, 15)),
            ("15/01/2024", datetime(2024, 1, 15)),
            ("Q1 2024", datetime(2024, 3, 31)),
            ("2024", datetime(2024, 12, 31))
        ]
        
        for date_str, expected in test_cases:
            result = funding_parser.parse_date(date_str)
            assert result.date() == expected.date()
    
    def test_extract_investors(self, funding_parser):
        """Test extraction of investor names from text."""
        text = "Led by Andreessen Horowitz with participation from Coinbase Ventures and Binance Labs"
        investors = funding_parser.extract_investors(text)
        
        expected_investors = ["Andreessen Horowitz", "Coinbase Ventures", "Binance Labs"]
        assert all(investor in investors for investor in expected_investors)
    
    def test_detect_round_type(self, funding_parser):
        """Test detection of funding round types."""
        test_cases = [
            ("Series A funding round", "Series A"),
            ("Seed round led by", "Seed"),
            ("Pre-seed investment", "Pre-Seed"),
            ("Series B extension", "Series B"),
            ("Strategic investment", "Strategic"),
            ("Token sale", "Token Sale")
        ]
        
        for text, expected in test_cases:
            result = funding_parser.detect_round_type(text)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_parse_funding_data(self, funding_parser, sample_funding_data):
        """Test complete funding data parsing."""
        with patch.object(funding_parser, 'detect_category') as mock_detect:
            mock_detect.return_value = "DEFI"
            
            result = await funding_parser.parse_funding_data(sample_funding_data)
            
            assert result["project_name"] == "DeFi Protocol"
            assert result["amount_usd"] == 10000000
            assert result["round_type"] == "Series A"
            assert result["category"] == "DEFI"
            assert "Venture Capital A" in result["investors"]
    
    def test_normalize_project_name(self, funding_parser):
        """Test project name normalization."""
        test_cases = [
            ("DeFi Protocol Inc.", "DeFi Protocol"),
            ("Crypto Exchange Ltd", "Crypto Exchange"),
            ("  Blockchain  Company  ", "Blockchain Company"),
            ("NFT-Marketplace", "NFT Marketplace")
        ]
        
        for input_name, expected in test_cases:
            result = funding_parser.normalize_project_name(input_name)
            assert result == expected
    
    def test_extract_website_domain(self, funding_parser):
        """Test website domain extraction."""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://www.test.org", "test.org"),
            ("https://subdomain.example.io", "subdomain.example.io"),
            ("invalid-url", None)
        ]
        
        for url, expected in test_cases:
            result = funding_parser.extract_domain(url)
            assert result == expected


class TestCrawlerServices:
    """Test cases for web crawler services."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock HTTP session for testing."""
        session = Mock()
        session.get = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_fetch_page_content(self, mock_session):
        """Test fetching page content with proper error handling."""
        from app.services.crawler import WebCrawler
        
        crawler = WebCrawler(session=mock_session)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html>Test content</html>")
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        content = await crawler.fetch_page("https://example.com")
        assert "Test content" in content
    
    @pytest.mark.asyncio
    async def test_parse_funding_news(self, mock_session):
        """Test parsing funding news from web pages."""
        from app.services.crawler import FundingNewsCrawler
        
        crawler = FundingNewsCrawler(session=mock_session)
        
        sample_html = """
        <article>
            <h1>DeFi Protocol Raises $10M Series A</h1>
            <p>DeFi Protocol, a decentralized lending platform, announced today 
               that it has raised $10 million in Series A funding led by 
               Andreessen Horowitz.</p>
            <time>2024-01-15</time>
        </article>
        """
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_html)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        funding_data = await crawler.parse_funding_news("https://example.com/news")
        
        assert funding_data["project_name"] == "DeFi Protocol"
        assert funding_data["amount"] == "$10M"
        assert funding_data["round_type"] == "Series A"
    
    def test_extract_structured_data(self):
        """Test extraction of structured data from HTML."""
        from app.services.crawler import StructuredDataExtractor
        
        extractor = StructuredDataExtractor()
        
        html_with_json_ld = """
        <script type="application/ld+json">
        {
            "@type": "Organization",
            "name": "Crypto Company",
            "url": "https://crypto.com",
            "description": "A cryptocurrency exchange"
        }
        </script>
        """
        
        data = extractor.extract_json_ld(html_with_json_ld)
        assert data["name"] == "Crypto Company"
        assert data["@type"] == "Organization"


class TestEnrichmentServices:
    """Test cases for data enrichment services."""
    
    @pytest.fixture
    def enrichment_service(self):
        """Create enrichment service instance."""
        from app.services.enrichment import ProjectEnrichmentService
        return ProjectEnrichmentService()
    
    @pytest.mark.asyncio
    async def test_enrich_project_data(self, enrichment_service):
        """Test project data enrichment with external APIs."""
        project_data = {
            "name": "Uniswap",
            "website": "https://uniswap.org",
            "token_symbol": "UNI"
        }
        
        with patch.object(enrichment_service, 'fetch_token_data') as mock_token:
            mock_token.return_value = {
                "market_cap": 5000000000,
                "price": 25.50,
                "volume_24h": 100000000
            }
            
            enriched = await enrichment_service.enrich_project(project_data)
            
            assert enriched["market_cap"] == 5000000000
            assert enriched["token_price"] == 25.50
    
    @pytest.mark.asyncio
    async def test_fetch_social_metrics(self, enrichment_service):
        """Test fetching social media metrics."""
        with patch.object(enrichment_service, 'fetch_twitter_metrics') as mock_twitter:
            mock_twitter.return_value = {
                "followers": 50000,
                "tweets": 1200,
                "engagement_rate": 0.05
            }
            
            metrics = await enrichment_service.fetch_social_metrics("@uniswap")
            
            assert metrics["followers"] == 50000
            assert metrics["engagement_rate"] == 0.05
    
    def test_calculate_project_score(self, enrichment_service):
        """Test project scoring algorithm."""
        project_data = {
            "funding_total": 50000000,
            "market_cap": 1000000000,
            "social_followers": 100000,
            "github_stars": 5000,
            "team_size": 25
        }
        
        score = enrichment_service.calculate_score(project_data)
        
        assert 0 <= score <= 100
        assert isinstance(score, (int, float))
    
    @pytest.mark.asyncio
    async def test_validate_project_data(self, enrichment_service):
        """Test project data validation and cleaning."""
        raw_data = {
            "name": "  Test Project  ",
            "website": "invalid-url",
            "description": "A" * 1000,  # Too long
            "funding_amount": "not-a-number"
        }
        
        validated = await enrichment_service.validate_and_clean(raw_data)
        
        assert validated["name"] == "Test Project"
        assert validated["website"] is None
        assert len(validated["description"]) <= 500
        assert validated["funding_amount"] is None