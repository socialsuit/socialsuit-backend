"""Repository pattern implementation for database access.

This module provides base repository classes and utilities for implementing
the repository pattern with SQLAlchemy. It includes support for:
- Async sessions
- Transaction contexts
- Pagination helpers
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Select

from shared.database.pagination import Page, PageParams, paginate

# Type variable for the model
ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """Base repository for database operations.
    
    This class provides common database operations for a specific model type.
    It uses SQLAlchemy's async session for all database operations.
    
    Attributes:
        model: The SQLAlchemy model class this repository handles
    """
    
    def __init__(self, model: Type[ModelType]):
        """Initialize the repository with a model class.
        
        Args:
            model: The SQLAlchemy model class this repository handles
        """
        self.model = model
    
    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get a record by its ID.
        
        Args:
            db: The database session
            id: The ID of the record to get
            
        Returns:
            The record if found, None otherwise
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_all(self, db: AsyncSession) -> List[ModelType]:
        """Get all records.
        
        Args:
            db: The database session
            
        Returns:
            A list of all records
        """
        query = select(self.model)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_paginated(
        self, 
        db: AsyncSession, 
        page_params: PageParams,
        query: Optional[Select] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Page[ModelType]:
        """Get paginated records.
        
        Args:
            db: The database session
            page_params: Pagination parameters
            query: Optional custom query to use
            sort_by: Optional field to sort by
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            A Page object containing the records and pagination metadata
        """
        if query is None:
            query = select(self.model)
            
        if sort_by is not None:
            if hasattr(self.model, sort_by):
                order_func = asc if sort_order.lower() == "asc" else desc
                query = query.order_by(order_func(getattr(self.model, sort_by)))
        
        return await paginate(db, query, page_params)
    
    async def create(self, db: AsyncSession, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """Create a new record.
        
        Args:
            db: The database session
            obj_in: The data to create the record with
            
        Returns:
            The created record
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
            db_obj = self.model(**obj_in_data)
        else:
            db_obj = obj_in
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
        db_obj: ModelType, 
        obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """Update a record.
        
        Args:
            db: The database session
            db_obj: The database object to update
            obj_in: The data to update the record with
            
        Returns:
            The updated record
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Delete a record by its ID.
        
        Args:
            db: The database session
            id: The ID of the record to delete
            
        Returns:
            The deleted record if found, None otherwise
        """
        obj = await self.get_by_id(db, id)
        if obj is None:
            return None
            
        await db.delete(obj)
        await db.commit()
        return obj
    
    async def count(self, db: AsyncSession) -> int:
        """Count all records.
        
        Args:
            db: The database session
            
        Returns:
            The number of records
        """
        query = select(func.count()).select_from(self.model)
        result = await db.execute(query)
        return result.scalar_one()


@asynccontextmanager
async def transaction(db: AsyncSession):
    """Context manager for database transactions.
    
    This context manager ensures that all database operations within its scope
    are executed within a transaction. If an exception occurs, the transaction
    is rolled back. Otherwise, it is committed.
    
    Args:
        db: The database session
        
    Yields:
        The database session
    """
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise


def get_repository(model: Type[ModelType]) -> Type[BaseRepository[ModelType]]:
    """Factory function to create a repository for a specific model.
    
    Args:
        model: The SQLAlchemy model class
        
    Returns:
        A repository class for the specified model
    """
    return type(f"{model.__name__}Repository", (BaseRepository[model],), {"model": model})