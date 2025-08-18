import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any
import tempfile
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.database.base import Base
from app.models.project import Project
from app.models.funding_round import FundingRound
from app.crud.project import project_crud
from app.services.crawler import FundingNewsCrawler, ProjectCrawler
from app.services.funding_parser import FundingParser
from app.services.enrichment import ProjectEnrichmentService
from app.services.fuzzy_matcher import FuzzyMatcher
from app.core.database import get_db


class TestMiniCrawlToDBIntegration:
    """Integration tests for the complete mini-crawl to database workflow."""
    
    @pytest.fixture
    async def test_db(self):
        """Create a test database for integration testing."""
        # Use in-memory SQLite for testing
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        yield async_session
        
        await engine.dispose()
    
    @pytest.fixture
    def sample_funding_articles(self):
        """Sample funding articles for testing."""
        return [
            {
                "url": "https://techcrunch.com/2024/01/15/defi-startup-raises-50m",
                "html": """
                <article>
                    <h1>DeFi Protocol Raises $50M Series B</h1>
                    <div class="article-content">
                        <p>DeFi Protocol, a decentralized finance platform, announced today 
                           that it has raised $50 million in Series B funding led by 
                           Andreessen Horowitz, with participation from Coinbase Ventures.</p>
                        <p>The company, founded in 2022, operates at https://defiprotocol.com 
                           and has a token symbol DFP.</p>
                    </div>
                    <time datetime="2024-01-15T10:00:00Z">January 15, 2024</time>
                </article>
                """
            },
            {
                "url": "https://coindesk.com/2024/01/10/nft-marketplace-funding",
                "html": """
                <div class="article-wrap">
                    <h1>NFT Exchange Secures $25M in Seed Funding</h1>
                    <div class="entry-content">
                        <p>NFT Exchange, a new marketplace for digital collectibles, 
                           has secured $25 million in seed funding from Binance Labs.</p>
                        <p>Visit them at https://nftexchange.io with token NFX.</p>
                    </div>
                    <time>2024-01-10</time>
                </div>
                """
            }
        ]
    
    @pytest.mark.asyncio
    async def test_complete_crawl_to_db_workflow(self, test_db, sample_funding_articles):
        """Test the complete workflow from crawling to database storage."""
        async with test_db() as db:
            # Step 1: Mock the crawler to return sample articles
            crawler = FundingNewsCrawler()
            parser = FundingParser()
            enricher = ProjectEnrichmentService()
            matcher = FuzzyMatcher()
            
            with patch.object(crawler, 'fetch_page') as mock_fetch, \
                 patch.object(enricher, 'enrich_project') as mock_enrich:
                
                # Mock crawler responses
                mock_fetch.side_effect = [article["html"] for article in sample_funding_articles]
                
                # Mock enrichment responses
                mock_enrich.side_effect = [
                    {
                        "market_cap": 1000000000,
                        "token_price": 15.50,
                        "twitter_followers": 100000,
                        "project_score": 75.5
                    },
                    {
                        "market_cap": 500000000,
                        "token_price": 8.25,
                        "twitter_followers": 50000,
                        "project_score": 65.0
                    }
                ]
                
                # Step 2: Process each article
                processed_projects = []
                
                for article in sample_funding_articles:
                    # Crawl and parse
                    funding_data = await parser.parse_funding_data_from_html(
                        article["html"], article["url"]
                    )
                    
                    # Check for existing projects (fuzzy matching)
                    existing_project = await matcher.find_fuzzy_match(
                        db, funding_data["project_name"], 
                        funding_data.get("website"), 
                        funding_data.get("token_symbol")
                    )
                    
                    if existing_project:
                        # Update existing project
                        updated_project = await project_crud.update_with_category_detection(
                            db, db_obj=existing_project, obj_in=funding_data
                        )
                        processed_projects.append(updated_project)
                    else:
                        # Create new project
                        new_project = await project_crud.create_with_category_detection(
                            db, obj_in=funding_data
                        )
                        processed_projects.append(new_project)
                
                # Step 3: Verify results in database
                assert len(processed_projects) == 2
                
                # Verify first project (DeFi Protocol)
                defi_project = processed_projects[0]
                assert defi_project.name == "DeFi Protocol"
                assert defi_project.category == "DEFI"
                assert defi_project.website == "https://defiprotocol.com"
                assert defi_project.token_symbol == "DFP"
                
                # Verify second project (NFT Exchange)
                nft_project = processed_projects[1]
                assert nft_project.name == "NFT Exchange"
                assert nft_project.category == "NFT"
                assert nft_project.website == "https://nftexchange.io"
                assert nft_project.token_symbol == "NFX"
                
                # Verify funding rounds were created
                defi_funding = await db.execute(
                    "SELECT * FROM funding_rounds WHERE project_id = ?", 
                    (defi_project.id,)
                )
                assert defi_funding.fetchone() is not None
    
    @pytest.mark.asyncio
    async def test_duplicate_project_handling(self, test_db):
        """Test handling of duplicate projects during crawling."""
        async with test_db() as db:
            # Create an existing project
            existing_project_data = {
                "name": "Existing Protocol",
                "website": "https://existing.com",
                "token_symbol": "EXT",
                "category": "DEFI"
            }
            
            existing_project = await project_crud.create_with_category_detection(
                db, obj_in=existing_project_data
            )
            
            # Simulate crawling data for the same project
            crawler_data = {
                "project_name": "Existing Protocol Inc.",  # Slightly different name
                "website": "https://existing.com",
                "token_symbol": "EXT",
                "description": "Updated description",
                "funding_amount": 10000000
            }
            
            matcher = FuzzyMatcher()
            
            # Test fuzzy matching
            matched_project = await matcher.find_fuzzy_match(
                db, crawler_data["project_name"], 
                crawler_data["website"], 
                crawler_data["token_symbol"]
            )
            
            assert matched_project is not None
            assert matched_project.id == existing_project.id
            
            # Test updating existing project
            updated_project = await project_crud.update_with_category_detection(
                db, db_obj=matched_project, obj_in=crawler_data
            )
            
            assert updated_project.description == "Updated description"
            assert updated_project.total_funding == 10000000
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, test_db):
        """Test error handling throughout the crawl-to-DB workflow."""
        async with test_db() as db:
            crawler = FundingNewsCrawler()
            parser = FundingParser()
            
            # Test handling of malformed HTML
            malformed_html = "<html><body>Invalid article structure</body></html>"
            
            with patch.object(crawler, 'fetch_page', return_value=malformed_html):
                try:
                    funding_data = await parser.parse_funding_data_from_html(
                        malformed_html, "https://example.com/bad-article"
                    )
                    # Should handle gracefully and return minimal data
                    assert funding_data is not None
                    assert "project_name" in funding_data
                except Exception as e:
                    # Should not crash the entire workflow
                    assert "parsing" in str(e).lower()
            
            # Test handling of database errors
            invalid_project_data = {
                "name": None,  # Invalid - name is required
                "website": "invalid-url"
            }
            
            with pytest.raises(Exception):
                await project_crud.create_with_category_detection(
                    db, obj_in=invalid_project_data
                )
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, test_db):
        """Test performance of batch processing multiple articles."""
        async with test_db() as db:
            # Generate multiple sample articles
            num_articles = 50
            sample_articles = []
            
            for i in range(num_articles):
                article_html = f"""
                <article>
                    <h1>Project {i} Raises $10M</h1>
                    <p>Project {i} has raised funding from investors.</p>
                    <p>Website: https://project{i}.com</p>
                    <time>2024-01-{i % 28 + 1:02d}</time>
                </article>
                """
                sample_articles.append(article_html)
            
            crawler = FundingNewsCrawler()
            parser = FundingParser()
            
            with patch.object(crawler, 'fetch_page') as mock_fetch:
                mock_fetch.side_effect = sample_articles
                
                start_time = datetime.now()
                
                # Process articles in batches
                batch_size = 10
                processed_count = 0
                
                for i in range(0, num_articles, batch_size):
                    batch = sample_articles[i:i + batch_size]
                    
                    # Process batch concurrently
                    tasks = []
                    for j, html in enumerate(batch):
                        task = parser.parse_funding_data_from_html(
                            html, f"https://example.com/article-{i+j}"
                        )
                        tasks.append(task)
                    
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Store successful results
                    for result in batch_results:
                        if not isinstance(result, Exception):
                            try:
                                await project_crud.create_with_category_detection(
                                    db, obj_in=result
                                )
                                processed_count += 1
                            except Exception:
                                pass  # Skip duplicates or invalid data
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Verify performance metrics
                assert processed_count > 0
                assert processing_time < 30  # Should complete within 30 seconds
                
                # Verify data was stored correctly
                all_projects = await project_crud.get_multi(db, limit=100)
                assert len(all_projects) >= processed_count
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_workflow(self, test_db):
        """Test data consistency throughout the entire workflow."""
        async with test_db() as db:
            # Original article data
            article_html = """
            <article>
                <h1>Consistency Test Protocol Raises $100M Series C</h1>
                <div class="content">
                    <p>Consistency Test Protocol, a blockchain infrastructure company, 
                       announced a $100 million Series C round led by Sequoia Capital.</p>
                    <p>Founded in 2021, the company operates at https://consistency.test 
                       with token symbol CST.</p>
                    <p>The funding will be used to expand their Layer 2 scaling solution.</p>
                </div>
                <time datetime="2024-01-20T14:00:00Z">January 20, 2024</time>
            </article>
            """
            
            crawler = FundingNewsCrawler()
            parser = FundingParser()
            enricher = ProjectEnrichmentService()
            
            with patch.object(crawler, 'fetch_page', return_value=article_html), \
                 patch.object(enricher, 'enrich_project') as mock_enrich:
                
                mock_enrich.return_value = {
                    "market_cap": 2000000000,
                    "token_price": 50.0,
                    "project_score": 88.5
                }
                
                # Step 1: Parse funding data
                funding_data = await parser.parse_funding_data_from_html(
                    article_html, "https://example.com/consistency-test"
                )
                
                # Verify parsed data
                assert funding_data["project_name"] == "Consistency Test Protocol"
                assert funding_data["funding_amount"] == 100000000
                assert funding_data["round_type"] == "Series C"
                assert funding_data["website"] == "https://consistency.test"
                assert funding_data["token_symbol"] == "CST"
                assert "Sequoia Capital" in funding_data["investors"]
                
                # Step 2: Create project in database
                created_project = await project_crud.create_with_category_detection(
                    db, obj_in=funding_data
                )
                
                # Verify database consistency
                assert created_project.name == funding_data["project_name"]
                assert created_project.website == funding_data["website"]
                assert created_project.token_symbol == funding_data["token_symbol"]
                assert created_project.category == "LAYER_2"  # Should be auto-detected
                assert created_project.total_funding == funding_data["funding_amount"]
                
                # Step 3: Verify funding round was created
                funding_rounds = await db.execute(
                    "SELECT * FROM funding_rounds WHERE project_id = ?",
                    (created_project.id,)
                )
                funding_round = funding_rounds.fetchone()
                
                assert funding_round is not None
                assert funding_round.amount == 100000000
                assert funding_round.round_type == "Series C"
                assert "Sequoia Capital" in funding_round.investors
                
                # Step 4: Verify enriched data consistency
                enriched_project = await enricher.enrich_project({
                    "id": created_project.id,
                    "name": created_project.name,
                    "token_symbol": created_project.token_symbol
                })
                
                assert enriched_project["market_cap"] == 2000000000
                assert enriched_project["project_score"] == 88.5


class TestCrawlerServiceIntegration:
    """Integration tests for crawler services working together."""
    
    @pytest.mark.asyncio
    async def test_multi_source_crawling(self):
        """Test crawling from multiple news sources simultaneously."""
        sources = [
            "https://techcrunch.com/funding",
            "https://coindesk.com/business",
            "https://cointelegraph.com/news"
        ]
        
        crawler = FundingNewsCrawler()
        
        with patch.object(crawler, 'fetch_page') as mock_fetch:
            # Mock responses from different sources
            mock_responses = [
                "<article><h1>TechCrunch: Project A raises $10M</h1></article>",
                "<div><h1>CoinDesk: Project B secures $20M</h1></div>",
                "<article><h1>Cointelegraph: Project C gets $30M</h1></article>"
            ]
            mock_fetch.side_effect = mock_responses
            
            # Crawl all sources concurrently
            tasks = [crawler.crawl_funding_news(url) for url in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify results from all sources
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= 2  # At least 2 sources should succeed
    
    @pytest.mark.asyncio
    async def test_rate_limiting_compliance(self):
        """Test that crawlers respect rate limiting."""
        crawler = FundingNewsCrawler(rate_limit=2)  # 2 requests per second
        
        urls = [f"https://example.com/article-{i}" for i in range(5)]
        
        with patch.object(crawler, 'fetch_page', return_value="<html>Test</html>"):
            start_time = datetime.now()
            
            # Crawl multiple URLs
            tasks = [crawler.crawl_with_rate_limit(url) for url in urls]
            await asyncio.gather(*tasks)
            
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            
            # Should take at least 2 seconds due to rate limiting
            assert elapsed_time >= 2.0