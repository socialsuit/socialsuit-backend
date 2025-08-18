"""CRUD operations for Project model."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi.encoders import jsonable_encoder

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.category_detector import category_detector
from app.crud.base import CRUDBase


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """CRUD operations for Project model."""
    
    def create_with_category_detection(self, db: Session, *, obj_in: ProjectCreate, auto_detect_category: bool = True) -> Project:
        """Create a new project with automatic category detection."""
        obj_in_data = jsonable_encoder(obj_in)
        
        # Auto-detect category if not provided and auto_detect_category is True
        if auto_detect_category and not obj_in_data.get('category'):
            detected_category = category_detector.detect_category(
                name=obj_in_data.get('name'),
                description=obj_in_data.get('description'),
                website=obj_in_data.get('website'),
                token_symbol=obj_in_data.get('token_symbol')
            )
            if detected_category:
                obj_in_data['category'] = detected_category
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_with_category_detection(self, db: Session, *, db_obj: Project, obj_in: ProjectUpdate, auto_detect_category: bool = True) -> Project:
        """Update a project with automatic category detection."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # Auto-detect category if not provided in update and auto_detect_category is True
        if auto_detect_category and 'category' not in update_data:
            # Use updated fields if available, otherwise use existing data
            name = update_data.get('name', obj_data.get('name'))
            description = update_data.get('description', obj_data.get('description'))
            website = update_data.get('website', obj_data.get('website'))
            token_symbol = update_data.get('token_symbol', obj_data.get('token_symbol'))
            
            detected_category = category_detector.detect_category(
                name=name,
                description=description,
                website=website,
                token_symbol=token_symbol
            )
            if detected_category and detected_category != obj_data.get('category'):
                update_data['category'] = detected_category
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects by category."""
        return (
            db.query(self.model)
            .filter(self.model.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_multi_with_filters(self, 
                              db: Session, 
                              *, 
                              skip: int = 0, 
                              limit: int = 100,
                              category: Optional[str] = None,
                              search: Optional[str] = None,
                              token_symbol: Optional[str] = None) -> List[Project]:
        """Get multiple projects with various filters."""
        query = db.query(self.model)
        
        # Apply category filter
        if category:
            query = query.filter(self.model.category == category)
        
        # Apply search filter (name, description, website)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.description.ilike(search_term),
                    self.model.website.ilike(search_term),
                    self.model.slug.ilike(search_term)
                )
            )
        
        # Apply token symbol filter
        if token_symbol:
            query = query.filter(self.model.token_symbol.ilike(f"%{token_symbol}%"))
        
        return query.offset(skip).limit(limit).all()
    
    def count_with_filters(self, 
                          db: Session, 
                          *, 
                          category: Optional[str] = None,
                          search: Optional[str] = None,
                          token_symbol: Optional[str] = None) -> int:
        """Count projects with filters."""
        query = db.query(func.count(self.model.id))
        
        # Apply category filter
        if category:
            query = query.filter(self.model.category == category)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.description.ilike(search_term),
                    self.model.website.ilike(search_term),
                    self.model.slug.ilike(search_term)
                )
            )
        
        # Apply token symbol filter
        if token_symbol:
            query = query.filter(self.model.token_symbol.ilike(f"%{token_symbol}%"))
        
        return query.scalar()
    
    def get_category_stats(self, db: Session) -> List[Dict[str, Any]]:
        """Get statistics for each project category."""
        total_projects = db.query(func.count(self.model.id)).scalar()
        
        category_stats = (
            db.query(
                self.model.category,
                func.count(self.model.id).label('count')
            )
            .filter(self.model.category.isnot(None))
            .group_by(self.model.category)
            .all()
        )
        
        # Calculate percentages
        stats = []
        for category, count in category_stats:
            percentage = (count / total_projects * 100) if total_projects > 0 else 0
            stats.append({
                'category': category,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Add uncategorized projects
        uncategorized_count = (
            db.query(func.count(self.model.id))
            .filter(self.model.category.is_(None))
            .scalar()
        )
        
        if uncategorized_count > 0:
            percentage = (uncategorized_count / total_projects * 100) if total_projects > 0 else 0
            stats.append({
                'category': 'uncategorized',
                'count': uncategorized_count,
                'percentage': round(percentage, 2)
            })
        
        return sorted(stats, key=lambda x: x['count'], reverse=True)
    
    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Project]:
        """Get project by slug."""
        return db.query(self.model).filter(self.model.slug == slug).first()
    
    def get_by_token_symbol(self, db: Session, *, token_symbol: str) -> Optional[Project]:
        """Get project by token symbol."""
        return db.query(self.model).filter(self.model.token_symbol == token_symbol).first()
    
    def get_by_website_domain(self, db: Session, *, domain: str) -> Optional[Project]:
        """Get project by website domain."""
        return (
            db.query(self.model)
            .filter(self.model.website.ilike(f"%{domain}%"))
            .first()
        )
    
    def bulk_update_categories(self, db: Session, *, auto_detect: bool = True) -> int:
        """Bulk update categories for projects that don't have one."""
        if not auto_detect:
            return 0
        
        projects_without_category = (
            db.query(self.model)
            .filter(self.model.category.is_(None))
            .all()
        )
        
        updated_count = 0
        for project in projects_without_category:
            detected_category = category_detector.detect_category(
                name=project.name,
                description=project.description,
                website=project.website,
                token_symbol=project.token_symbol
            )
            
            if detected_category:
                project.category = detected_category
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
        
        return updated_count
    
    def fuzzy_match_and_update(self, db: Session, *, name: str = None, slug: str = None, 
                              domain: str = None, token_symbol: str = None) -> Optional[Project]:
        """Fuzzy match project and update category if missing."""
        project = None
        
        # Try exact matches first
        if slug:
            project = self.get_by_slug(db, slug=slug)
        
        if not project and token_symbol:
            project = self.get_by_token_symbol(db, token_symbol=token_symbol)
        
        if not project and domain:
            project = self.get_by_website_domain(db, domain=domain)
        
        # Try fuzzy name matching
        if not project and name:
            # Simple fuzzy matching - can be enhanced with more sophisticated algorithms
            similar_projects = (
                db.query(self.model)
                .filter(self.model.name.ilike(f"%{name}%"))
                .limit(5)
                .all()
            )
            
            if similar_projects:
                # For now, take the first match - can be improved with similarity scoring
                project = similar_projects[0]
        
        # Update category if project found and category is missing
        if project and not project.category:
            detected_category = category_detector.detect_category(
                name=project.name,
                description=project.description,
                website=project.website,
                token_symbol=project.token_symbol
            )
            
            if detected_category:
                project.category = detected_category
                db.commit()
                db.refresh(project)
        
        return project


project = CRUDProject(Project)