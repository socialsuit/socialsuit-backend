"""Tests for the enrichment service and tasks."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.enrichment import EnrichmentService, GitHubAdapter, WebsiteCrawler, TokenInfoAdapter
from app.models.project import Project
from app.core.database import AsyncSessionLocal


class TestGitHubAdapter:
    """Test GitHub adapter functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_repo_stats_success(self):
        """Test successful GitHub repository stats fetching."""
        adapter = GitHubAdapter()
        
        # Mock the _fetch_repo_data method directly
        mock_response = {
            'stargazers_count': 150,
            'forks_count': 25,
            'open_issues_count': 8,
            'watchers_count': 45,
            'created_at': '2023-01-15T10:30:00Z',
            'updated_at': '2024-01-15T15:45:00Z',
            'pushed_at': '2024-01-15T15:45:00Z',
            'default_branch': 'main',
            'size': 1024,
            'language': 'Python',
            'license': {'name': 'MIT'},
            'topics': ['blockchain', 'defi', 'ethereum'],
            'description': 'Test repository',
            'homepage': 'https://example.com'
        }
        
        with patch.object(adapter, '_fetch_repo_data', return_value=mock_response):
            result = await adapter.fetch_repo_stats('https://github.com/ethereum/go-ethereum')
            
            assert result is not None
            assert result['stars'] == 150
            assert result['forks'] == 25
            assert result['open_issues'] == 8
            assert result['watchers'] == 45
            assert result['language'] == 'Python'
            assert result['topics'] == ['blockchain', 'defi', 'ethereum']


@pytest.mark.asyncio
async def test_acceptance_criteria():
    """
    Acceptance test: Running enrichment task adds GitHub stats for a test project.
    """
    # This test simulates the acceptance criteria
    # In a real scenario, this would use a test database with actual project data
    
    async with AsyncSessionLocal() as db:
        service = EnrichmentService(db)
        
        # Mock a project with GitHub URL
        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.name = 'Ethereum'
        mock_project.github_url = 'https://github.com/ethereum/go-ethereum'
        mock_project.website_url = 'https://ethereum.org'
        mock_project.meta_data = {}
        
        # Mock database operations
        with patch.object(db, 'execute') as mock_execute:
            with patch.object(db, 'commit'):
                mock_result = Mock()
                mock_result.scalar_one_or_none.return_value = mock_project
                mock_execute.return_value = mock_result
                
                # Mock GitHub adapter to return realistic data
                with patch.object(service.github_adapter, 'fetch_repo_stats') as mock_github:
                    mock_github.return_value = {
                        'stars': 45000,
                        'forks': 18000,
                        'open_issues': 250,
                        'watchers': 3500,
                        'language': 'Go',
                        'topics': ['blockchain', 'ethereum', 'cryptocurrency'],
                        'created_at': '2013-12-26T13:05:46Z',
                        'updated_at': '2024-01-15T10:30:00Z'
                    }
                    
                    # Mock other adapters
                    with patch.object(service.website_crawler, 'crawl_website') as mock_website:
                        with patch.object(service.token_adapter, 'fetch_token_info') as mock_token:
                            mock_website.return_value = {
                                'title': 'Ethereum',
                                'description': 'Decentralized platform for smart contracts'
                            }
                            mock_token.return_value = {'placeholder': True}
                            
                            # Run enrichment
                            success = await service.enrich_project(1)
                            
                            # Verify enrichment was successful
                            assert success is True
                            
                            # Verify GitHub stats were added
                            enrichment_data = mock_project.meta_data['enrichment']
                            github_data = enrichment_data['github']
                            
                            assert github_data['stars'] == 45000
                            assert github_data['forks'] == 18000
                            assert github_data['language'] == 'Go'
                            assert 'blockchain' in github_data['topics']
                            
                            # Verify enrichment history was recorded
                            history = mock_project.meta_data['enrichment_history']
                            assert len(history) > 0
                            assert history[-1]['success'] is True
                            assert 'github' in history[-1]['adapters']
                            
                            print("✅ Acceptance criteria met: GitHub stats successfully added to project")