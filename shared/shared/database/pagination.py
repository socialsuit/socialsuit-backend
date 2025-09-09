"""Database pagination utilities.

This module provides utilities for paginating database queries.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from math import ceil

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


T = TypeVar('T')


class Page(BaseModel, Generic[T]):
    """A paginated response model."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
    
    def dict_with_metadata(self) -> Dict[str, Any]:
        """Return a dictionary with items and pagination metadata."""
        return {
            "items": self.items,
            "metadata": {
                "total": self.total,
                "page": self.page,
                "size": self.size,
                "pages": self.pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
            }
        }


async def paginate_query(
    session: AsyncSession,
    query: Select,
    page: int = 1,
    size: int = 10,
) -> Page[Any]:
    """Paginate a SQLAlchemy query.
    
    Args:
        session: The database session
        query: The SQLAlchemy select query to paginate
        page: The page number (1-indexed)
        size: The page size
        
    Returns:
        A Page object containing the paginated results
    """
    # Ensure page and size are valid
    if page < 1:
        page = 1
    if size < 1:
        size = 10
    
    # Calculate offset
    offset = (page - 1) * size
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Apply pagination
    paginated_query = query.offset(offset).limit(size)
    result = await session.execute(paginated_query)
    items = result.scalars().all()
    
    # Calculate total pages
    pages = ceil(total / size) if total > 0 else 1
    
    return Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )