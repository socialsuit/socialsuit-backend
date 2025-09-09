"""User service implementation.

This module provides services for user-related operations.
"""

from typing import List, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from shared.database.pagination import Page


class UserService:
    """Service for user-related operations.
    
    This service uses the UserRepository for database operations and provides
    business logic for user-related operations.
    """
    
    def __init__(self, repository: UserRepository = Depends()):
        """Initialize the service with a repository.
        
        Args:
            repository: The user repository
        """
        self.repository = repository
    
    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            db: The database session
            user_id: The user ID
            
        Returns:
            The user if found, None otherwise
        """
        return await self.repository.get_by_id(db, user_id)
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email.
        
        Args:
            db: The database session
            email: The email to search for
            
        Returns:
            The user if found, None otherwise
        """
        return await self.repository.get_by_email(db, email)
    
    async def get_all(self, db: AsyncSession) -> List[User]:
        """Get all users.
        
        Args:
            db: The database session
            
        Returns:
            A list of all users
        """
        return await self.repository.get_all(db)
    
    async def get_active_users(self, db: AsyncSession) -> List[User]:
        """Get all active users.
        
        Args:
            db: The database session
            
        Returns:
            A list of active users
        """
        return await self.repository.get_active_users(db)
    
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
        return await self.repository.get_active_users_paginated(db, page, size)
    
    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Create a new user.
        
        Args:
            db: The database session
            user_in: The user data
            
        Returns:
            The created user
        """
        # Hash the password
        hashed_password = get_password_hash(user_in.password)
        user_data = user_in.dict(exclude={"password"})
        user_data["hashed_password"] = hashed_password
        
        return await self.repository.create(db, user_data)
    
    async def update(self, db: AsyncSession, user: User, user_in: UserUpdate) -> User:
        """Update a user.
        
        Args:
            db: The database session
            user: The user to update
            user_in: The user data
            
        Returns:
            The updated user
        """
        update_data = user_in.dict(exclude_unset=True)
        
        # Hash the password if provided
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        return await self.repository.update(db, user, update_data)
    
    async def delete(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Delete a user.
        
        Args:
            db: The database session
            user_id: The user ID
            
        Returns:
            The deleted user if found, None otherwise
        """
        return await self.repository.delete(db, user_id)
    
    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user.
        
        Args:
            db: The database session
            email: The user email
            password: The user password
            
        Returns:
            The authenticated user if valid, None otherwise
        """
        user = await self.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user