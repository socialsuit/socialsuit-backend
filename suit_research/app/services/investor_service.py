"""Investor service for managing investor profiles and portfolios."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from fuzzywuzzy import fuzz
import re
import logging

from app.models.investor import Investor, InvestorPortfolio
from app.models.project import Project
from app.models.funding import FundingRound

logger = logging.getLogger(__name__)


class InvestorService:
    """Service for investor-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fuzzy_threshold = 85  # Minimum similarity score for fuzzy matching
    
    async def get_investors(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Investor]:
        """Get list of investors with optional search."""
        query = select(Investor).options(selectinload(Investor.portfolios))
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Investor.name.ilike(search_pattern),
                    Investor.slug.ilike(search_pattern)
                )
            )
        
        query = query.offset(skip).limit(limit).order_by(Investor.name)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_investor_by_id(self, investor_id: int) -> Optional[Investor]:
        """Get investor by ID with portfolio information."""
        query = select(Investor).options(
            selectinload(Investor.portfolios).selectinload(InvestorPortfolio.project)
        ).where(Investor.id == investor_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_investor_portfolio(self, investor_id: int) -> List[Project]:
        """Get portfolio projects for an investor."""
        query = select(Project).join(
            InvestorPortfolio, Project.id == InvestorPortfolio.project_id
        ).where(InvestorPortfolio.investor_id == investor_id)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create_investor(self, investor_data: Dict[str, Any]) -> Investor:
        """Create new investor."""
        # Generate slug from name
        slug = self._generate_slug(investor_data["name"])
        investor_data["slug"] = slug
        
        investor = Investor(**investor_data)
        self.db.add(investor)
        await self.db.commit()
        await self.db.refresh(investor)
        return investor
    
    async def update_investor(
        self, 
        investor_id: int, 
        investor_data: Dict[str, Any]
    ) -> Optional[Investor]:
        """Update investor information."""
        investor = await self.get_investor_by_id(investor_id)
        if not investor:
            return None
        
        for key, value in investor_data.items():
            if hasattr(investor, key):
                setattr(investor, key, value)
        
        await self.db.commit()
        await self.db.refresh(investor)
        return investor
    
    async def parse_investor_from_funding(self, funding_round: FundingRound) -> List[Investor]:
        """Parse and create/update investors from funding round data."""
        if not funding_round.investors:
            return []
        
        created_investors = []
        
        for investor_info in funding_round.investors:
            if isinstance(investor_info, str):
                investor_name = investor_info
                investor_data = {"name": investor_name}
            elif isinstance(investor_info, dict):
                investor_name = investor_info.get("name", "")
                investor_data = investor_info
            else:
                continue
            
            if not investor_name:
                continue
            
            # Try to find existing investor by fuzzy matching
            existing_investor = await self._find_investor_by_fuzzy_name(investor_name)
            
            if existing_investor:
                # Update existing investor with new information
                updated_investor = await self._update_investor_profile(
                    existing_investor, investor_data
                )
                created_investors.append(updated_investor)
            else:
                # Create new investor
                try:
                    new_investor = await self.create_investor(investor_data)
                    created_investors.append(new_investor)
                except Exception as e:
                    logger.error(f"Failed to create investor {investor_name}: {e}")
                    continue
        
        return created_investors
    
    async def link_funding_to_investors(self, funding_round: FundingRound) -> None:
        """Link funding events to investor profiles and update portfolios."""
        investors = await self.parse_investor_from_funding(funding_round)
        
        for investor in investors:
            # Check if portfolio relationship already exists
            existing_portfolio = await self._get_portfolio_relationship(
                investor.id, funding_round.project_id
            )
            
            if not existing_portfolio:
                # Create new portfolio relationship
                portfolio = InvestorPortfolio(
                    investor_id=investor.id,
                    project_id=funding_round.project_id,
                    first_invested_at=funding_round.announced_at
                )
                self.db.add(portfolio)
            else:
                # Update first investment date if this is earlier
                if (funding_round.announced_at and 
                    (not existing_portfolio.first_invested_at or 
                     funding_round.announced_at < existing_portfolio.first_invested_at)):
                    existing_portfolio.first_invested_at = funding_round.announced_at
        
        await self.db.commit()
    
    async def _find_investor_by_fuzzy_name(self, name: str) -> Optional[Investor]:
        """Find investor using fuzzy name matching."""
        # First try exact match
        query = select(Investor).where(Investor.name.ilike(f"%{name}%"))
        result = await self.db.execute(query)
        exact_match = result.scalar_one_or_none()
        
        if exact_match:
            return exact_match
        
        # Get all investors for fuzzy matching
        query = select(Investor)
        result = await self.db.execute(query)
        all_investors = result.scalars().all()
        
        best_match = None
        best_score = 0
        
        normalized_name = self._normalize_name(name)
        
        for investor in all_investors:
            normalized_investor_name = self._normalize_name(investor.name)
            
            # Calculate similarity scores
            ratio_score = fuzz.ratio(normalized_name, normalized_investor_name)
            partial_score = fuzz.partial_ratio(normalized_name, normalized_investor_name)
            token_score = fuzz.token_sort_ratio(normalized_name, normalized_investor_name)
            
            # Use the highest score
            max_score = max(ratio_score, partial_score, token_score)
            
            if max_score > best_score and max_score >= self.fuzzy_threshold:
                best_score = max_score
                best_match = investor
        
        return best_match
    
    async def _get_portfolio_relationship(
        self, 
        investor_id: int, 
        project_id: int
    ) -> Optional[InvestorPortfolio]:
        """Get existing portfolio relationship."""
        query = select(InvestorPortfolio).where(
            and_(
                InvestorPortfolio.investor_id == investor_id,
                InvestorPortfolio.project_id == project_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _update_investor_profile(
        self, 
        investor: Investor, 
        new_data: Dict[str, Any]
    ) -> Investor:
        """Update investor profile with new information."""
        # Update basic fields
        if "website" in new_data and new_data["website"] and not investor.website:
            investor.website = new_data["website"]
        
        # Merge profile data
        if "profile" in new_data or any(key in new_data for key in ["bio", "social_links", "description"]):
            current_profile = investor.profile or {}
            
            # Update bio
            if "bio" in new_data:
                current_profile["bio"] = new_data["bio"]
            
            # Update social links
            if "social_links" in new_data:
                current_profile["social_links"] = new_data["social_links"]
            
            # Update description
            if "description" in new_data:
                current_profile["description"] = new_data["description"]
            
            # Merge additional profile data
            if "profile" in new_data and isinstance(new_data["profile"], dict):
                current_profile.update(new_data["profile"])
            
            investor.profile = current_profile
        
        await self.db.commit()
        await self.db.refresh(investor)
        return investor
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for better matching."""
        # Remove common suffixes and prefixes
        name = re.sub(r'\b(llc|inc|corp|ltd|limited|ventures|capital|partners|fund|management)\b', '', name.lower())
        # Remove extra whitespace and special characters
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        return slug