"""User repository implementation.

This module provides a repository for user-related database operations.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from shared.database.repository import BaseRepository
from shared.database.pagination import Page, paginate_query


class UserRepository(BaseRepository[User]):
    """Repository for user-related database operations."""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email.
        
        Args:
            db: The database session
            email: The email to search for
            
        Returns:
            The user if found, None otherwise
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_active_users(self, db: AsyncSession) -> List[User]:
        """Get all active users.
        
        Args:
            db: The database session
            
        Returns:
            A list of active users
        """
        query = select(User).where(User.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_active_users_paginated(
        self, 
        db: AsyncSession, 
        page: int = 1, 
        size: int = 10
    ) -> Page[User]:
        """Get paginated active users.
        
        Args:
            db: The database session
            page: The page number
            size: The page size
            
        Returns:
            A Page object containing active users
        """
        query = select(User).where(User.is_active == True)
        return await paginate_query(db, query, page, size)