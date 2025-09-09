"""Database connection utilities.

This module provides utilities for managing database connections.
"""

from typing import AsyncGenerator, Optional

from sqlalchemy import URL, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


def create_db_engine(
    driver: str,
    username: str,
    password: str,
    host: str,
    port: int,
    database: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    **kwargs
) -> AsyncEngine:
    """Create a SQLAlchemy async engine.
    
    Args:
        driver: The database driver (e.g., 'postgresql+asyncpg')
        username: The database username
        password: The database password
        host: The database host
        port: The database port
        database: The database name
        echo: Whether to echo SQL statements
        pool_size: The connection pool size
        max_overflow: The maximum number of connections to overflow
        **kwargs: Additional arguments to pass to create_async_engine
        
    Returns:
        An async SQLAlchemy engine
    """
    url = URL.create(
        drivername=driver,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    
    return create_async_engine(
        url,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        **kwargs
    )


async def get_db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session from an engine.
    
    Args:
        engine: The SQLAlchemy async engine
        
    Yields:
        An async SQLAlchemy session
    """
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise