"""Enhanced fuzzy matching service with category support."""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz
import re
from urllib.parse import urlparse

from app.crud.project import project as project_crud
from app.services.category_detector import ProjectCategoryDetector
from app.models.project import Project


class FuzzyMatcher:
    """Enhanced fuzzy matching with category support."""
    
    def __init__(self):
        self.category_detector = ProjectCategoryDetector()
        self.min_similarity_threshold = 80
        self.domain_threshold = 90
        self.token_threshold = 95
    
    async def find_and_update_matches(
        self,
        db: Session,
        project_data: Dict[str, Any],
        update_category: bool = True
    ) -> Optional[Project]:
        """
        Find fuzzy matches for a project and update category if missing.
        
        Args:
            db: Database session
            project_data: Project data to match against
            update_category: Whether to update category if missing
            
        Returns:
            Matched project if found, None otherwise
        """
        name = project_data.get('name', '')
        website = project_data.get('website', '')
        token_symbol = project_data.get('token_symbol', '')
        description = project_data.get('description', '')
        
        # Try exact matches first
        exact_match = await self._find_exact_matches(db, name, website, token_symbol)
        if exact_match:
            if update_category and not exact_match.category:
                await self._update_project_category(db, exact_match, project_data)
            return exact_match
        
        # Try fuzzy matches
        fuzzy_match = await self._find_fuzzy_matches(db, name, description)
        if fuzzy_match:
            if update_category and not fuzzy_match.category:
                await self._update_project_category(db, fuzzy_match, project_data)
            return fuzzy_match
        
        return None
    
    async def _find_exact_matches(
        self,
        db: Session,
        name: str,
        website: str,
        token_symbol: str
    ) -> Optional[Project]:
        """Find exact matches by domain, token symbol, or slug."""
        
        # Match by domain
        if website:
            domain = self._extract_domain(website)
            if domain:
                project = await project_crud.get_by_website_domain(db, domain)
                if project:
                    return project
        
        # Match by token symbol
        if token_symbol:
            project = await project_crud.get_by_token_symbol(db, token_symbol)
            if project:
                return project
        
        # Match by slug (generated from name)
        if name:
            slug = self._generate_slug(name)
            project = await project_crud.get_by_slug(db, slug)
            if project:
                return project
        
        return None
    
    async def _find_fuzzy_matches(
        self,
        db: Session,
        name: str,
        description: str
    ) -> Optional[Project]:
        """Find fuzzy matches by name similarity."""
        
        if not name:
            return None
        
        # Get all projects for fuzzy matching
        projects = await project_crud.get_multi(db, limit=1000)
        
        best_match = None
        best_score = 0
        
        for project in projects:
            # Calculate name similarity
            name_score = fuzz.ratio(name.lower(), project.name.lower())
            
            # Boost score if descriptions are similar
            desc_score = 0
            if description and project.description:
                desc_score = fuzz.partial_ratio(
                    description.lower()[:200],
                    project.description.lower()[:200]
                )
            
            # Combined score with name weighted more heavily
            combined_score = (name_score * 0.7) + (desc_score * 0.3)
            
            if combined_score > best_score and combined_score >= self.min_similarity_threshold:
                best_score = combined_score
                best_match = project
        
        return best_match
    
    async def _update_project_category(
        self,
        db: Session,
        project: Project,
        project_data: Dict[str, Any]
    ) -> None:
        """Update project category if missing."""
        
        # Detect category from the new project data
        category = self.category_detector.detect_category(
            name=project_data.get('name', project.name),
            description=project_data.get('description', project.description),
            website=project_data.get('website', project.website),
            token_symbol=project_data.get('token_symbol', project.token_symbol)
        )
        
        if category:
            # Update the project with the detected category
            await project_crud.update(
                db=db,
                db_obj=project,
                obj_in={'category': category}
            )
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url if url.startswith(('http://', 'https://')) else f'https://{url}')
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'[\s-]+', '-', slug)
        return slug.strip('-')
    
    async def bulk_update_categories(
        self,
        db: Session,
        limit: int = 100
    ) -> Dict[str, int]:
        """Bulk update categories for projects that don't have one."""
        
        # Get projects without categories
        projects = await project_crud.get_projects_without_category(db, limit=limit)
        
        updated_count = 0
        categories_assigned = {}
        
        for project in projects:
            category = self.category_detector.detect_category(
                name=project.name,
                description=project.description,
                website=project.website,
                token_symbol=project.token_symbol
            )
            
            if category:
                await project_crud.update(
                    db=db,
                    db_obj=project,
                    obj_in={'category': category}
                )
                updated_count += 1
                categories_assigned[category] = categories_assigned.get(category, 0) + 1
        
        return {
            'updated_count': updated_count,
            'categories_assigned': categories_assigned
        }


# Global instance
fuzzy_matcher = FuzzyMatcher()