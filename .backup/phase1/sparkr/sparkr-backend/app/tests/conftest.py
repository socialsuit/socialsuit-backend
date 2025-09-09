import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.db.session import get_session
from app.core.config import settings

# Test database URL - use an in-memory SQLite database for testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def session(test_engine):
    """Create a test database session"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def override_get_session(session):
    """Override the get_session dependency"""
    async def _override_get_session():
        yield session
    
    return _override_get_session


@pytest.fixture
async def async_client(override_get_session):
    """Create an async test client"""
    app.dependency_overrides[get_session] = override_get_session
    
    # Create client with ASGITransport instead of passing app directly
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    # Cleanup happens automatically with async with
    app.dependency_overrides.clear()