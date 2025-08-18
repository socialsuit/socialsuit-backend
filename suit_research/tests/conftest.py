import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.core.database import get_db
from app.models.project import Project
from app.models.funding_round import FundingRound
from app.crud.project import project_crud
from app.services.category_detector import ProjectCategoryDetector
from app.services.fuzzy_matcher import FuzzyMatcher


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def override_get_db(test_db: AsyncSession):
    """Override the get_db dependency for testing."""
    async def _override_get_db():
        yield test_db
    
    return _override_get_db


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test DeFi Protocol",
        "description": "A decentralized finance protocol for testing",
        "website": "https://testdefi.com",
        "token_symbol": "TDF",
        "category": "DEFI",
        "total_funding": 10000000,
        "team_size": 15,
        "founded_year": 2022
    }


@pytest.fixture
def sample_funding_round_data():
    """Sample funding round data for testing."""
    return {
        "amount": 5000000,
        "currency": "USD",
        "round_type": "Series A",
        "date": "2024-01-15",
        "investors": ["Venture Capital A", "Crypto Fund B"],
        "valuation": 50000000
    }


@pytest.fixture
def sample_funding_article_html():
    """Sample funding article HTML for testing."""
    return """
    <article>
        <h1>Test Protocol Raises $10M Series A</h1>
        <div class="article-content">
            <p>Test Protocol, a decentralized finance platform, announced today 
               that it has raised $10 million in Series A funding led by 
               Andreessen Horowitz, with participation from Coinbase Ventures.</p>
            <p>The company operates at https://testprotocol.com with token TTP.</p>
            <p>Founded in 2022, the team of 20 engineers plans to use the funding 
               to expand their DeFi lending products.</p>
        </div>
        <time datetime="2024-01-15T10:00:00Z">January 15, 2024</time>
    </article>
    """


@pytest.fixture
def mock_http_session():
    """Mock HTTP session for testing web requests."""
    session = Mock()
    session.get = Mock()
    return session


@pytest.fixture
def mock_api_responses():
    """Mock API responses for external services."""
    return {
        "coingecko": {
            "market_data": {
                "current_price": {"usd": 25.50},
                "market_cap": {"usd": 1000000000},
                "total_volume": {"usd": 50000000},
                "price_change_percentage_24h": 5.2
            },
            "community_data": {
                "twitter_followers": 100000,
                "reddit_subscribers": 25000
            }
        },
        "twitter": {
            "data": {
                "public_metrics": {
                    "followers_count": 100000,
                    "following_count": 500,
                    "tweet_count": 2500,
                    "listed_count": 1000
                }
            }
        },
        "github": {
            "stargazers_count": 5000,
            "forks_count": 1200,
            "watchers_count": 800,
            "open_issues_count": 50,
            "language": "Solidity",
            "created_at": "2022-01-15T10:00:00Z",
            "updated_at": "2024-01-15T15:30:00Z"
        }
    }


@pytest.fixture
async def sample_project(test_db: AsyncSession, sample_project_data):
    """Create a sample project in the test database."""
    project = await project_crud.create_with_category_detection(
        test_db, obj_in=sample_project_data
    )
    return project


@pytest.fixture
def category_detector():
    """Create a category detector instance for testing."""
    return ProjectCategoryDetector()


@pytest.fixture
def fuzzy_matcher():
    """Create a fuzzy matcher instance for testing."""
    return FuzzyMatcher()


@pytest.fixture
def mock_external_apis():
    """Mock external API calls for testing."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        yield mock_get


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    # Any cleanup code can go here


# Custom pytest markers
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "crawler: marks tests as crawler tests"
    )


@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_project_data(name: str = "Test Project", **kwargs):
        """Create project data with optional overrides."""
        default_data = {
            "name": name,
            "description": f"Description for {name}",
            "website": f"https://{name.lower().replace(' ', '')}.com",
            "token_symbol": name[:3].upper(),
            "category": "DEFI",
            "total_funding": 1000000,
            "team_size": 10,
            "founded_year": 2023
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_funding_round_data(amount: int = 1000000, **kwargs):
        """Create funding round data with optional overrides."""
        default_data = {
            "amount": amount,
            "currency": "USD",
            "round_type": "Seed",
            "date": "2024-01-15",
            "investors": ["Test Investor"],
            "valuation": amount * 10
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_article_html(project_name: str, amount: str = "$10M", **kwargs):
        """Create article HTML with optional overrides."""
        default_data = {
            "title": f"{project_name} Raises {amount}",
            "content": f"{project_name} has raised {amount} in funding.",
            "date": "2024-01-15",
            "investors": "Test Investor"
        }
        default_data.update(kwargs)
        
        return f"""
        <article>
            <h1>{default_data['title']}</h1>
            <div class="content">
                <p>{default_data['content']}</p>
                <p>Led by {default_data['investors']}.</p>
            </div>
            <time>{default_data['date']}</time>
        </article>
        """


@pytest.fixture
def test_data_factory():
    """Provide the test data factory."""
    return TestDataFactory


# Performance testing utilities
@pytest.fixture
def performance_monitor():
    """Monitor test performance."""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed_time(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return PerformanceMonitor()


# Database utilities for testing
class DatabaseTestUtils:
    """Utilities for database testing."""
    
    @staticmethod
    async def clear_all_tables(db: AsyncSession):
        """Clear all tables in the test database."""
        await db.execute("DELETE FROM funding_rounds")
        await db.execute("DELETE FROM projects")
        await db.commit()
    
    @staticmethod
    async def count_records(db: AsyncSession, table_name: str) -> int:
        """Count records in a table."""
        result = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
        return result.scalar()


@pytest.fixture
def db_utils():
    """Provide database testing utilities."""
    return DatabaseTestUtils