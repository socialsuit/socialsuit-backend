"""Tests for the repository pattern implementation.

This module provides tests for the repository pattern implementation.
"""

import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, List, Optional, Type

from sqlalchemy import Column, Integer, String, Boolean, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from shared.database.repository import BaseRepository, transaction
from shared.database.session import DatabaseSessionManager

# Create a test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create a base model for tests
Base = declarative_base()


class TestUser(Base):
    """Test user model for repository tests."""
    __tablename__ = "test_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)


class TestUserRepository(BaseRepository[TestUser]):
    """Test user repository for repository tests."""
    
    def __init__(self):
        super().__init__(TestUser)
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[TestUser]:
        """Get a user by email."""
        query = select(TestUser).where(TestUser.email == email)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_active_users(self, db: AsyncSession) -> List[TestUser]:
        """Get all active users."""
        query = select(TestUser).where(TestUser.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()


@pytest_asyncio.fixture
async def db_session_manager() -> AsyncGenerator[DatabaseSessionManager, None]:
    """Create a database session manager for tests."""
    # Create the session manager
    session_manager = DatabaseSessionManager(TEST_DATABASE_URL)
    
    # Create the tables
    async with session_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield session_manager
    
    # Drop the tables
    async with session_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Close the engine
    await session_manager.close()


@pytest_asyncio.fixture
async def db_session(db_session_manager: DatabaseSessionManager) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for tests."""
    async with db_session_manager.session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a user."""
    # Arrange
    repo = TestUserRepository()
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }
    
    # Act
    user = await repo.create(db_session, user_data)
    
    # Assert
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.name == user_data["name"]
    assert user.is_active == user_data["is_active"]


@pytest.mark.asyncio
async def test_get_by_id(db_session: AsyncSession):
    """Test getting a user by ID."""
    # Arrange
    repo = TestUserRepository()
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }
    user = await repo.create(db_session, user_data)
    
    # Act
    retrieved_user = await repo.get_by_id(db_session, user.id)
    
    # Assert
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


@pytest.mark.asyncio
async def test_get_by_email(db_session: AsyncSession):
    """Test getting a user by email."""
    # Arrange
    repo = TestUserRepository()
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }
    user = await repo.create(db_session, user_data)
    
    # Act
    retrieved_user = await repo.get_by_email(db_session, user.email)
    
    # Assert
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession):
    """Test updating a user."""
    # Arrange
    repo = TestUserRepository()
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }
    user = await repo.create(db_session, user_data)
    
    # Act
    update_data = {"name": "Updated Name"}
    updated_user = await repo.update(db_session, user, update_data)
    
    # Assert
    assert updated_user.name == update_data["name"]
    assert updated_user.email == user.email  # Unchanged


@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession):
    """Test deleting a user."""
    # Arrange
    repo = TestUserRepository()
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }
    user = await repo.create(db_session, user_data)
    
    # Act
    deleted_user = await repo.delete(db_session, user.id)
    
    # Assert
    assert deleted_user is not None
    assert deleted_user.id == user.id
    
    # Verify the user is deleted
    retrieved_user = await repo.get_by_id(db_session, user.id)
    assert retrieved_user is None


@pytest.mark.asyncio
async def test_get_all_users(db_session: AsyncSession):
    """Test getting all users."""
    # Arrange
    repo = TestUserRepository()
    user_data_list = [
        {"email": "user1@example.com", "name": "User 1", "is_active": True},
        {"email": "user2@example.com", "name": "User 2", "is_active": True},
        {"email": "user3@example.com", "name": "User 3", "is_active": False},
    ]
    
    for user_data in user_data_list:
        await repo.create(db_session, user_data)
    
    # Act
    all_users = await repo.get_all(db_session)
    
    # Assert
    assert len(all_users) == len(user_data_list)


@pytest.mark.asyncio
async def test_get_active_users(db_session: AsyncSession):
    """Test getting active users."""
    # Arrange
    repo = TestUserRepository()
    user_data_list = [
        {"email": "user1@example.com", "name": "User 1", "is_active": True},
        {"email": "user2@example.com", "name": "User 2", "is_active": True},
        {"email": "user3@example.com", "name": "User 3", "is_active": False},
    ]
    
    for user_data in user_data_list:
        await repo.create(db_session, user_data)
    
    # Act
    active_users = await repo.get_active_users(db_session)
    
    # Assert
    assert len(active_users) == 2  # Only the active users


@pytest.mark.asyncio
async def test_transaction_commit(db_session_manager: DatabaseSessionManager):
    """Test transaction commit."""
    # Arrange
    repo = TestUserRepository()
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }
    
    # Act - Create a user within a transaction
    async with db_session_manager.transaction() as session:
        await repo.create(session, user_data)
    
    # Assert - The user should be committed
    async with db_session_manager.session() as session:
        retrieved_user = await repo.get_by_email(session, user_data["email"])
        assert retrieved_user is not None
        assert retrieved_user.email == user_data["email"]


@pytest.mark.asyncio
async def test_transaction_rollback(db_session_manager: DatabaseSessionManager):
    """Test transaction rollback."""
    # Arrange
    repo = TestUserRepository()
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }
    
    # Act - Try to create a user within a transaction that raises an exception
    try:
        async with db_session_manager.transaction() as session:
            await repo.create(session, user_data)
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # Assert - The user should be rolled back
    async with db_session_manager.session() as session:
        retrieved_user = await repo.get_by_email(session, user_data["email"])
        assert retrieved_user is None  # The user should not exist