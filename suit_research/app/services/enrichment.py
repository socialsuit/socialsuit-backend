"""Enrichment service for project data enhancement."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.project import Project
from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubAdapter:
    """Adapter for fetching GitHub repository data."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or getattr(settings, 'GITHUB_TOKEN', None)
        self.base_url = "https://api.github.com"
        
    async def fetch_repo_stats(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch GitHub repository statistics.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Dictionary containing stars, forks, commits, and other stats
        """
        try:
            # Extract owner and repo from URL
            owner, repo = self._parse_github_url(repo_url)
            if not owner or not repo:
                return None
                
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
                headers['Accept'] = 'application/vnd.github.v3+json'
            
            async with aiohttp.ClientSession(headers=headers) as session:
                # Fetch repository data
                repo_data = await self._fetch_repo_data(session, owner, repo)
                if not repo_data:
                    return None
                
                return {
                    'stars': repo_data.get('stargazers_count', 0),
                    'forks': repo_data.get('forks_count', 0),
                    'watchers': repo_data.get('watchers_count', 0),
                    'open_issues': repo_data.get('open_issues_count', 0),
                    'language': repo_data.get('language'),
                    'created_at': repo_data.get('created_at'),
                    'updated_at': repo_data.get('updated_at'),
                    'pushed_at': repo_data.get('pushed_at'),
                    'default_branch': repo_data.get('default_branch'),
                    'size': repo_data.get('size', 0),
                    'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
                    'topics': repo_data.get('topics', []),
                    'description': repo_data.get('description'),
                    'homepage': repo_data.get('homepage')
                }
                
        except Exception as e:
            logger.error(f"Error fetching GitHub stats for {repo_url}: {e}")
            return None
    
    def _parse_github_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Parse GitHub URL to extract owner and repository name."""
        try:
            # Handle various GitHub URL formats
            patterns = [
                r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
                r'github\.com/([^/]+)/([^/]+)/.*'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1), match.group(2)
            
            return None, None
        except Exception:
            return None, None
    
    async def _fetch_repo_data(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch basic repository data."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return {}


class WebsiteCrawler:
    """Crawler for extracting project information from websites."""
    
    def __init__(self):
        self.timeout = 30
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    async def crawl_website(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Crawl project website for description and whitepaper links.
        
        Args:
            url: Website URL to crawl
            
        Returns:
            Dictionary containing description, whitepaper links, and other metadata
        """
        try:
            headers = {'User-Agent': self.user_agent}
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else None
                    
                    # Extract description
                    description = self._extract_description(soup)
                    
                    # Find whitepaper links
                    whitepaper_links = self._find_whitepaper_links(soup, url)
                    
                    # Extract social media links
                    social_links = self._extract_social_links(soup)
                    
                    # Extract contact information
                    contact_info = self._extract_contact_info(soup)
                    
                    return {
                        'title': title_text,
                        'description': description,
                        'whitepaper_links': whitepaper_links,
                        'social_links': social_links,
                        'contact_info': contact_info,
                        'crawled_at': datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error crawling website {url}: {e}")
            return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract project description from various sources."""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return None
    
    def _find_whitepaper_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find whitepaper download links."""
        whitepaper_links = []
        
        # Look for links containing whitepaper-related keywords
        keywords = ['whitepaper', 'white paper', 'technical paper', 'documentation', 'docs']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().lower()
            
            # Check if link text or href contains whitepaper keywords
            if any(keyword in text for keyword in keywords) or any(keyword in href.lower() for keyword in keywords):
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                if absolute_url not in whitepaper_links:
                    whitepaper_links.append(absolute_url)
        
        return whitepaper_links
    
    def _extract_social_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links."""
        social_links = {}
        social_patterns = {
            'twitter': r'twitter\.com/[^/\s]+',
            'telegram': r't\.me/[^/\s]+',
            'discord': r'discord\.(gg|com)/[^/\s]+',
            'github': r'github\.com/[^/\s]+',
            'medium': r'medium\.com/[^/\s]+',
            'linkedin': r'linkedin\.com/[^/\s]+'
        }
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    social_links[platform] = href
                    break
        
        return social_links
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> List[str]:
        """Extract contact information."""
        contact_info = []
        
        # Look for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = soup.get_text()
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info.extend(list(set(emails)))
        
        return contact_info


class TokenInfoAdapter:
    """Adapter for fetching token information (placeholder for external API integration)."""
    
    def __init__(self):
        # Placeholder for external API configuration
        self.api_key = getattr(settings, 'TOKEN_API_KEY', None)
        
    async def fetch_token_info(self, token_symbol: str, contract_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch token information from external APIs.
        
        Args:
            token_symbol: Token symbol (e.g., 'BTC', 'ETH')
            contract_address: Token contract address (optional)
            
        Returns:
            Dictionary containing token information
        """
        # Placeholder implementation
        # In a real implementation, this would integrate with APIs like:
        # - CoinGecko
        # - CoinMarketCap
        # - DeFiPulse
        # - Custom token APIs
        
        try:
            # Simulated token data structure
            return {
                'placeholder': True,
                'symbol': token_symbol,
                'contract_address': contract_address,
                'last_updated': datetime.utcnow().isoformat(),
                'api_source': 'placeholder'
            }
        except Exception as e:
            logger.error(f"Error fetching token info for {token_symbol}: {e}")
            return {}


class EnrichmentService:
    """Main service for project data enrichment."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.github_adapter = GitHubAdapter()
        self.website_crawler = WebsiteCrawler()
        self.token_adapter = TokenInfoAdapter()
        
    async def enrich_project(self, project_id: int, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enrich a project with data from various sources.
        
        Args:
            project_id: ID of the project to enrich
            config: Optional configuration for enrichment
            
        Returns:
            True if enrichment was successful, False otherwise
        """
        try:
            # Fetch project from database
            result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                logger.error(f"Project with ID {project_id} not found")
                return False
            
            enrichment_data = {}
            adapters_used = []
            
            # GitHub enrichment
            if project.github_url:
                logger.info(f"Enriching GitHub data for project {project.name}")
                github_data = await self.github_adapter.fetch_repo_stats(project.github_url)
                if github_data:
                    enrichment_data['github'] = github_data
                    adapters_used.append('github')
            
            # Website enrichment
            if project.website_url:
                logger.info(f"Enriching website data for project {project.name}")
                website_data = await self.website_crawler.crawl_website(project.website_url)
                if website_data:
                    enrichment_data['website'] = website_data
                    adapters_used.append('website')
            
            # Token enrichment
            if hasattr(project, 'token_symbol') and project.token_symbol:
                logger.info(f"Enriching token data for project {project.name}")
                token_data = await self.token_adapter.fetch_token_info(project.token_symbol)
                if token_data:
                    enrichment_data['token'] = token_data
                    adapters_used.append('token')
            
            # Update project metadata
            await self._update_project_metadata(project, enrichment_data, adapters_used)
            
            return True
            
        except Exception as e:
            logger.error(f"Error enriching project {project_id}: {e}")
            return False
    
    async def _update_project_metadata(self, project: Project, enrichment_data: Dict[str, Any], adapters_used: List[str]):
        """Update project metadata with enrichment data."""
        try:
            # Get existing metadata or create new
            current_metadata = project.meta_data or {}
            
            # Update enrichment data
            current_metadata['enrichment'] = enrichment_data
            current_metadata['last_enriched'] = datetime.utcnow().isoformat()
            
            # Add to enrichment history
            if 'enrichment_history' not in current_metadata:
                current_metadata['enrichment_history'] = []
            
            history_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'adapters': adapters_used,
                'success': True,
                'data_points': sum(len(data) if isinstance(data, dict) else 1 for data in enrichment_data.values())
            }
            
            current_metadata['enrichment_history'].append(history_entry)
            
            # Keep only last 50 history entries
            if len(current_metadata['enrichment_history']) > 50:
                current_metadata['enrichment_history'] = current_metadata['enrichment_history'][-50:]
            
            # Update project
            project.meta_data = current_metadata
            
            # Commit changes
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating project metadata: {e}")
            await self.db.rollback()
            raise
    
    async def get_enrichment_data(self, project_id: int) -> Dict[str, Any]:
        """Get current enrichment data for a project."""
        try:
            result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project or not project.meta_data:
                return {}
            
            return project.meta_data.get('enrichment', {})
            
        except Exception as e:
            logger.error(f"Error getting enrichment data for project {project_id}: {e}")
            return {}
    
    async def get_enrichment_history(self, project_id: int) -> List[Dict[str, Any]]:
        """Get enrichment history for a project."""
        try:
            result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project or not project.meta_data:
                return []
            
            return project.meta_data.get('enrichment_history', [])
            
        except Exception as e:
            logger.error(f"Error getting enrichment history for project {project_id}: {e}")
            return []