import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from services.database.database import get_db

# Import Base from a different location to avoid model conflicts
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

TestBase = declarative_base()

# Define minimal test models
class TestUser(TestBase):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    scheduled_posts = relationship("TestScheduledPost", back_populates="user")

class PostStatus(str, enum.Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"

class TestScheduledPost(TestBase):
    __tablename__ = "scheduled_posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String)
    post_payload = Column(JSON)
    scheduled_time = Column(DateTime)
    status = Column(String, default=PostStatus.PENDING)
    user = relationship("TestUser", back_populates="scheduled_posts")

class TestPostEngagement(TestBase):
    __tablename__ = "post_engagements"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String)
    platform = Column(String)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    views = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())

class TestUserMetrics(TestBase):
    __tablename__ = "user_metrics"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    platform = Column(String)
    followers = Column(Integer, default=0)
    engagement_rate = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())

class TestContentPerformance(TestBase):
    __tablename__ = "content_performance"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    platform = Column(String)
    content_type = Column(String)
    performance_score = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())

# Mock the database connection for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for testing
def setup_database():
    # We're using our test-specific models that are already imported
    # No need to import the original ScheduledPost model
    
    # Drop all tables first
    TestBase.metadata.drop_all(bind=engine)
    
    # Then create them
    TestBase.metadata.create_all(bind=engine)

# Initialize the database
setup_database()

# Override the get_db dependency
@pytest.fixture(scope="function")
def override_get_db():
    # Reset the database for each test
    setup_database()
    
    # Create a new session for the test
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

# Override the get_db function for testing
@pytest.fixture(scope="function")
def app_with_db(monkeypatch, override_get_db):
    # Use the override_get_db fixture to ensure database is reset
    def mock_get_db():
        yield from override_get_db
    
    # Apply the monkeypatch
    import services.database.database
    monkeypatch.setattr(services.database.database, "get_db", mock_get_db)
    
    # Import app after patching
    from main import app
    return app

@pytest.fixture(scope="function")
async def async_client(app_with_db):
    async with AsyncClient(app=app_with_db, base_url="http://test") as client:
        yield client
