"""Celery tasks for project enrichment operations."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from celery import current_task
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.enrichment import EnrichmentService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def enrich_project_task(self, project_id: int, config: Optional[Dict[str, Any]] = None):
    """
    Celery task for enriching a project with data from various sources.
    
    Args:
        project_id: ID of the project to enrich
        config: Optional configuration for enrichment process
    """
    config = config or {}
    
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Starting enrichment',
                'project_id': project_id,
                'config': config,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Run the async enrichment
        result = asyncio.run(_run_enrichment(project_id, config))
        
        # Update task status with results
        current_task.update_state(
            state='SUCCESS',
            meta={
                'status': 'completed',
                'project_id': project_id,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in enrichment task for project {project_id}: {e}")
        
        # Update task status with error
        current_task.update_state(
            state='FAILURE',
            meta={
                'status': 'failed',
                'project_id': project_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        raise


@celery_app.task(bind=True)
def bulk_enrich_projects_task(self, project_ids: list[int], config: Optional[Dict[str, Any]] = None):
    """
    Celery task for bulk enrichment of multiple projects.
    
    Args:
        project_ids: List of project IDs to enrich
        config: Optional configuration for enrichment process
    """
    config = config or {}
    results = []
    
    try:
        total_projects = len(project_ids)
        
        for i, project_id in enumerate(project_ids):
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Enriching project {i+1} of {total_projects}',
                        'current_project_id': project_id,
                        'progress': (i / total_projects) * 100,
                        'completed': i,
                        'total': total_projects,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                # Run enrichment for current project
                result = asyncio.run(_run_enrichment(project_id, config))
                results.append(result)
                
                logger.info(f"Completed enrichment for project {project_id}")
                
            except Exception as e:
                logger.error(f"Error enriching project {project_id}: {e}")
                results.append({
                    'project_id': project_id,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Final status update
        successful = len([r for r in results if r.get('status') == 'completed'])
        failed = len(results) - successful
        
        current_task.update_state(
            state='SUCCESS',
            meta={
                'status': 'bulk_enrichment_completed',
                'total_projects': total_projects,
                'successful': successful,
                'failed': failed,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'total_projects': total_projects,
            'successful': successful,
            'failed': failed,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk enrichment task: {e}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'status': 'bulk_enrichment_failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        raise


@celery_app.task(bind=True)
def scheduled_enrichment_task(self, config: Optional[Dict[str, Any]] = None):
    """
    Scheduled task for enriching projects that need updates.
    
    Args:
        config: Configuration including:
            - max_projects: Maximum number of projects to enrich (default: 50)
            - min_age_hours: Minimum hours since last enrichment (default: 24)
            - priority_projects: List of project IDs to prioritize
    """
    config = config or {}
    max_projects = config.get('max_projects', 50)
    min_age_hours = config.get('min_age_hours', 24)
    priority_projects = config.get('priority_projects', [])
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Finding projects for enrichment',
                'config': config,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Find projects that need enrichment
        project_ids = asyncio.run(_find_projects_for_enrichment(max_projects, min_age_hours, priority_projects))
        
        if not project_ids:
            return {
                'status': 'no_projects_found',
                'message': 'No projects found that need enrichment',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Run bulk enrichment
        logger.info(f"Starting scheduled enrichment for {len(project_ids)} projects")
        result = bulk_enrich_projects_task.apply_async(args=[project_ids, config])
        
        return {
            'status': 'scheduled_enrichment_started',
            'project_count': len(project_ids),
            'project_ids': project_ids,
            'bulk_task_id': result.id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in scheduled enrichment task: {e}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'status': 'scheduled_enrichment_failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        raise


async def _run_enrichment(project_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run enrichment for a single project.
    
    Args:
        project_id: ID of the project to enrich
        config: Enrichment configuration
        
    Returns:
        Enrichment result
    """
    async with AsyncSessionLocal() as db:
        enrichment_service = EnrichmentService(db)
        return await enrichment_service.enrich_project(project_id)


async def _find_projects_for_enrichment(
    max_projects: int, 
    min_age_hours: int, 
    priority_projects: list[int]
) -> list[int]:
    """
    Find projects that need enrichment.
    
    Args:
        max_projects: Maximum number of projects to return
        min_age_hours: Minimum hours since last enrichment
        priority_projects: List of project IDs to prioritize
        
    Returns:
        List of project IDs that need enrichment
    """
    from sqlalchemy import select, func, text
    from app.models.project import Project
    from datetime import timedelta
    
    async with AsyncSessionLocal() as db:
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=min_age_hours)
            
            # Build query for projects that need enrichment
            query = select(Project.id).where(
                # Projects that have never been enriched OR
                # were last enriched before the cutoff time
                (Project.meta_data.is_(None)) |
                (Project.meta_data['last_enriched'].astext.is_(None)) |
                (func.to_timestamp(Project.meta_data['last_enriched'].astext, 'YYYY-MM-DD"T"HH24:MI:SS.US') < cutoff_time)
            ).limit(max_projects)
            
            result = await db.execute(query)
            project_ids = [row[0] for row in result.fetchall()]
            
            # Prioritize specific projects if provided
            if priority_projects:
                # Move priority projects to the front
                prioritized = []
                remaining = []
                
                for pid in project_ids:
                    if pid in priority_projects:
                        prioritized.append(pid)
                    else:
                        remaining.append(pid)
                
                project_ids = prioritized + remaining
            
            logger.info(f"Found {len(project_ids)} projects for enrichment")
            return project_ids
            
        except Exception as e:
            logger.error(f"Error finding projects for enrichment: {e}")
            return []


# Periodic task registration (if using Celery Beat)
# This would typically be configured in celery beat schedule
@celery_app.task
def daily_enrichment_task():
    """Daily scheduled enrichment task."""
    config = {
        'max_projects': 100,
        'min_age_hours': 24
    }
    return scheduled_enrichment_task.delay(config)


@celery_app.task
def weekly_full_enrichment_task():
    """Weekly full enrichment task for all projects."""
    config = {
        'max_projects': 1000,
        'min_age_hours': 168  # 1 week
    }
    return scheduled_enrichment_task.delay(config)