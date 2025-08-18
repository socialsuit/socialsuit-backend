"""
Research service for business logic.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.research import Research, ResearchCategory


class ResearchService:
    """Service for research-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_research_list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Research]:
        """Get list of research items."""
        query = select(Research)
        
        if status:
            query = query.where(Research.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Research.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_research_by_id(self, research_id: int) -> Optional[Research]:
        """Get research by ID."""
        query = select(Research).where(Research.id == research_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_research(self, research_data: Dict[str, Any]) -> Research:
        """Create new research item."""
        research = Research(**research_data)
        self.db.add(research)
        await self.db.commit()
        await self.db.refresh(research)
        return research
    
    async def update_research(
        self, 
        research_id: int, 
        research_data: Dict[str, Any]
    ) -> Optional[Research]:
        """Update research item."""
        research = await self.get_research_by_id(research_id)
        if not research:
            return None
        
        for key, value in research_data.items():
            if hasattr(research, key):
                setattr(research, key, value)
        
        await self.db.commit()
        await self.db.refresh(research)
        return research
    
    async def delete_research(self, research_id: int) -> bool:
        """Delete research item."""
        research = await self.get_research_by_id(research_id)
        if not research:
            return False
        
        await self.db.delete(research)
        await self.db.commit()
        return True
    
    async def search_research(
        self, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Research]:
        """Search research items by title or content."""
        search_query = select(Research).where(
            Research.title.ilike(f"%{query}%") |
            Research.description.ilike(f"%{query}%")
        ).offset(skip).limit(limit).order_by(Research.created_at.desc())
        
        result = await self.db.execute(search_query)
        return result.scalars().all()