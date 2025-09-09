"""Database session management utilities.

This module provides utilities for managing database sessions and transactions.
"""

from typing import AsyncGenerator, Callable, Optional, TypeVar
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


T = TypeVar('T')


class DatabaseSessionManager:
    """Database session manager for async SQLAlchemy sessions.
    
    This class provides utilities for creating and managing async database sessions.
    It supports dependency injection for FastAPI and transaction management.
    """
    
    def __init__(self, database_url: str):
        """Initialize the session manager.
        
        Args:
            database_url: The SQLAlchemy database URL
        """
        self.engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )
        self.session_maker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
        )
    
    async def close(self):
        """Close the database engine."""
        if self.engine is not None:
            await self.engine.dispose()
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session.
        
        This context manager ensures that the session is closed after use.
        
        Yields:
            An async SQLAlchemy session
        """
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with transaction management.
        
        This context manager ensures that all database operations within its scope
        are executed within a transaction. If an exception occurs, the transaction
        is rolled back. Otherwise, it is committed.
        
        Yields:
            An async SQLAlchemy session
        """
        async with self.session() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
    
    def get_db(self) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
        """Get a database session dependency for FastAPI.
        
        Returns:
            A dependency that yields a database session
        """
        async def _get_db() -> AsyncGenerator[AsyncSession, None]:
            async with self.session() as session:
                yield session
        
        return _get_db


async def init_models(engine, base: DeclarativeBase):
    """Initialize database models.
    
    This function creates all tables defined in the base model.
    
    Args:
        engine: The SQLAlchemy engine
        base: The SQLAlchemy declarative base
    """
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)