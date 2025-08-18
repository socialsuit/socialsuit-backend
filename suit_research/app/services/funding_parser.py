"""Funding parser service for extracting and processing funding round data."""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from bs4 import BeautifulSoup
import dateutil.parser

from app.models.project import Project
from app.models.funding import FundingRound

logger = logging.getLogger(__name__)


class FundingParser:
    """Service for parsing funding announcements and extracting structured data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Currency conversion rates (simplified - in production use real-time API)
        self.currency_rates = {
            'USD': 1.0,
            'EUR': 1.1,
            'GBP': 1.25,
            'CAD': 0.75,
            'AUD': 0.65,
            'JPY': 0.007,
            'CHF': 1.05,
            'SGD': 0.73
        }
        
        # Round type mappings
        self.round_type_mappings = {
            'pre-seed': 'pre_seed',
            'preseed': 'pre_seed',
            'seed': 'seed',
            'series a': 'series_a',
            'series b': 'series_b',
            'series c': 'series_c',
            'series d': 'series_d',
            'series e': 'series_e',
            'series f': 'series_f',
            'bridge': 'bridge',
            'convertible': 'convertible',
            'debt': 'debt',
            'grant': 'grant',
            'ipo': 'ipo',
            'acquisition': 'acquisition'
        }
    
    async def parse_funding_announcement(
        self, 
        content: str, 
        source_url: str,
        content_type: str = 'html'
    ) -> Dict[str, Any]:
        """Parse funding announcement from HTML or JSON content."""
        try:
            if content_type.lower() == 'html':
                return await self._parse_html_content(content, source_url)
            elif content_type.lower() == 'json':
                return await self._parse_json_content(content, source_url)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error(f"Error parsing funding announcement: {e}")
            return {
                'success': False,
                'error': str(e),
                'source_url': source_url
            }
    
    async def _parse_html_content(self, html_content: str, source_url: str) -> Dict[str, Any]:
        """Parse HTML content to extract funding information."""
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()
        
        # Extract funding rounds using multiple patterns
        funding_rounds = self._extract_funding_rounds(text_content, source_url)
        
        # Process each funding round
        processed_rounds = []
        for round_data in funding_rounds:
            processed_round = await self._process_funding_round(round_data, source_url)
            if processed_round:
                processed_rounds.append(processed_round)
        
        return {
            'success': True,
            'funding_rounds': processed_rounds,
            'source_url': source_url,
            'parsed_at': datetime.now().isoformat()
        }
    
    async def _parse_json_content(self, json_content: str, source_url: str) -> Dict[str, Any]:
        """Parse JSON content to extract funding information."""
        try:
            data = json.loads(json_content)
            funding_rounds = []
            
            # Handle different JSON structures
            if isinstance(data, dict):
                if 'funding_rounds' in data:
                    funding_rounds = data['funding_rounds']
                elif 'investments' in data:
                    funding_rounds = data['investments']
                elif 'rounds' in data:
                    funding_rounds = data['rounds']
                else:
                    # Try to extract from the main data
                    funding_rounds = [data]
            elif isinstance(data, list):
                funding_rounds = data
            
            # Process each funding round
            processed_rounds = []
            for round_data in funding_rounds:
                processed_round = await self._process_json_funding_round(round_data, source_url)
                if processed_round:
                    processed_rounds.append(processed_round)
            
            return {
                'success': True,
                'funding_rounds': processed_rounds,
                'source_url': source_url,
                'parsed_at': datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON content: {e}")
            return {
                'success': False,
                'error': f"Invalid JSON: {str(e)}",
                'source_url': source_url
            }
    
    def _extract_funding_rounds(self, text_content: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract funding round information from text using regex patterns."""
        funding_rounds = []
        
        # Enhanced patterns for funding announcements
        patterns = [
            # "Company X raises $Y million in Series A"
            r'([A-Z][a-zA-Z0-9\s&.,-]+?)\s+(?:raises?|raised|secures?|secured|closes?|closed|announces?|announced)\s+\$([0-9,.]+)\s*(million|billion|thousand)?\s*(?:in\s+)?(Series\s+[A-Z]|seed|pre-seed|Series\s+[A-Z][0-9]*|bridge|convertible|debt|grant)?',
            
            # "$Y million Series A for Company X"
            r'\$([0-9,.]+)\s*(million|billion|thousand)?\s*(Series\s+[A-Z]|seed|pre-seed|bridge|convertible)?\s*(?:for|in|to|funding|round)\s+([A-Z][a-zA-Z0-9\s&.,-]+)',
            
            # "Company X's $Y million Series A"
            r"([A-Z][a-zA-Z0-9\s&.,-]+?)'s\s+\$([0-9,.]+)\s*(million|billion|thousand)?\s*(Series\s+[A-Z]|seed|pre-seed|bridge|convertible)?",
            
            # "Company X secures Series A funding of $Y million"
            r'([A-Z][a-zA-Z0-9\s&.,-]+?)\s+(?:secures?|secured|closes?|closed|raises?|raised)\s+(Series\s+[A-Z]|seed|pre-seed|bridge|convertible)\s+(?:funding|round)?\s*(?:of)?\s*\$([0-9,.]+)\s*(million|billion|thousand)?',
            
            # "Series A: Company X raises $Y million"
            r'(Series\s+[A-Z]|seed|pre-seed|bridge|convertible):\s*([A-Z][a-zA-Z0-9\s&.,-]+?)\s+(?:raises?|raised|secures?|secured)\s+\$([0-9,.]+)\s*(million|billion|thousand)?'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                funding_round = self._parse_funding_match(match, pattern, source_url)
                if funding_round:
                    funding_rounds.append(funding_round)
        
        # Remove duplicates based on company name and amount
        unique_rounds = self._remove_duplicate_rounds(funding_rounds)
        
        return unique_rounds
    
    def _parse_funding_match(self, match, pattern: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Parse a regex match into funding round data."""
        try:
            groups = match.groups()
            funding_round = {
                'source_url': source_url,
                'raw_text': match.group(0)
            }
            
            # Parse based on pattern structure
            if "raises" in pattern or "secures" in pattern:
                if len(groups) >= 2:
                    funding_round["company_name"] = self._clean_company_name(groups[0])
                    funding_round["amount_raw"] = groups[1]
                    
                    if len(groups) > 2 and groups[2]:
                        funding_round["amount_unit"] = groups[2].lower()
                    
                    if len(groups) > 3 and groups[3]:
                        funding_round["round_type"] = self._normalize_round_type(groups[3])
                        
            elif "for" in pattern or "to" in pattern:
                if len(groups) >= 2:
                    funding_round["amount_raw"] = groups[0]
                    
                    if len(groups) > 1 and groups[1]:
                        funding_round["amount_unit"] = groups[1].lower()
                    
                    if len(groups) > 2 and groups[2]:
                        funding_round["round_type"] = self._normalize_round_type(groups[2])
                    
                    if len(groups) > 3:
                        funding_round["company_name"] = self._clean_company_name(groups[3])
            
            # Calculate USD amount
            if 'amount_raw' in funding_round:
                funding_round['amount_usd'] = self._convert_to_usd(
                    funding_round['amount_raw'],
                    funding_round.get('amount_unit', 'million'),
                    'USD'  # Assume USD for now
                )
            
            # Extract announced date from surrounding text
            funding_round['announced_at'] = self._extract_date_from_context(
                match.group(0), source_url
            )
            
            # Extract investors from surrounding text
            funding_round['investors'] = self._extract_investors_from_context(
                match.group(0), source_url
            )
            
            return funding_round
            
        except Exception as e:
            logger.error(f"Error parsing funding match: {e}")
            return None
    
    async def _process_funding_round(self, round_data: Dict[str, Any], source_url: str) -> Optional[Dict[str, Any]]:
        """Process and enrich funding round data with fuzzy matching and confidence scoring."""
        try:
            company_name = round_data.get('company_name', '').strip()
            if not company_name:
                return None
            
            # Fuzzy match project
            project_match = await self._fuzzy_match_project(company_name)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(round_data, project_match)
            
            processed_round = {
                'project_name': company_name,
                'round_type': round_data.get('round_type', ''),
                'amount_usd': round_data.get('amount_usd'),
                'announced_at': round_data.get('announced_at'),
                'investors': round_data.get('investors', []),
                'source_url': source_url,
                'confidence_score': confidence_score,
                'project_match': project_match,
                'raw_data': round_data
            }
            
            return processed_round
            
        except Exception as e:
            logger.error(f"Error processing funding round: {e}")
            return None
    
    async def _process_json_funding_round(self, round_data: Dict[str, Any], source_url: str) -> Optional[Dict[str, Any]]:
        """Process funding round from JSON data."""
        try:
            # Extract fields from JSON structure
            company_name = (
                round_data.get('company_name') or 
                round_data.get('company') or 
                round_data.get('startup') or 
                round_data.get('project_name') or 
                round_data.get('name', '')
            ).strip()
            
            if not company_name:
                return None
            
            # Extract amount and convert to USD
            amount = round_data.get('amount') or round_data.get('funding_amount')
            currency = round_data.get('currency', 'USD')
            amount_usd = None
            
            if amount:
                if isinstance(amount, str):
                    # Parse amount string like "$5M" or "5 million"
                    amount_usd = self._parse_amount_string(amount, currency)
                else:
                    amount_usd = self._convert_to_usd(str(amount), 'raw', currency)
            
            # Extract round type
            round_type = self._normalize_round_type(
                round_data.get('round_type') or 
                round_data.get('stage') or 
                round_data.get('series', '')
            )
            
            # Extract date
            announced_at = self._parse_date(
                round_data.get('announced_at') or 
                round_data.get('date') or 
                round_data.get('announcement_date')
            )
            
            # Extract investors
            investors = round_data.get('investors', [])
            if isinstance(investors, str):
                investors = [inv.strip() for inv in investors.split(',')]
            
            # Fuzzy match project
            project_match = await self._fuzzy_match_project(company_name)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score({
                'company_name': company_name,
                'amount_usd': amount_usd,
                'round_type': round_type,
                'investors': investors
            }, project_match)
            
            processed_round = {
                'project_name': company_name,
                'round_type': round_type,
                'amount_usd': amount_usd,
                'announced_at': announced_at,
                'investors': investors,
                'source_url': source_url,
                'confidence_score': confidence_score,
                'project_match': project_match,
                'raw_data': round_data
            }
            
            return processed_round
            
        except Exception as e:
            logger.error(f"Error processing JSON funding round: {e}")
            return None
    
    async def _fuzzy_match_project(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Fuzzy match company name against existing projects."""
        try:
            # Query existing projects
            query = select(Project).where(
                or_(
                    Project.name.ilike(f"%{company_name}%"),
                    Project.slug.ilike(f"%{company_name.lower().replace(' ', '-')}%"),
                    Project.website.ilike(f"%{company_name.lower()}%")
                )
            ).limit(10)
            
            result = await self.db.execute(query)
            projects = result.scalars().all()
            
            best_match = None
            best_score = 0.0
            
            for project in projects:
                # Calculate similarity scores
                name_score = SequenceMatcher(None, company_name.lower(), project.name.lower()).ratio()
                slug_score = SequenceMatcher(None, company_name.lower().replace(' ', '-'), project.slug).ratio()
                
                # Check website domain match
                website_score = 0.0
                if project.website:
                    domain = urlparse(project.website).netloc.lower()
                    company_domain = company_name.lower().replace(' ', '').replace('.', '')
                    if company_domain in domain or domain.replace('.', '').replace('www', '') in company_domain:
                        website_score = 0.8
                
                # Combined score
                combined_score = max(name_score, slug_score, website_score)
                
                if combined_score > best_score and combined_score > 0.6:  # Minimum threshold
                    best_score = combined_score
                    best_match = {
                        'project_id': project.id,
                        'project_name': project.name,
                        'project_slug': project.slug,
                        'similarity_score': combined_score,
                        'match_type': 'name' if name_score == combined_score else ('slug' if slug_score == combined_score else 'website')
                    }
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return None
    
    def _calculate_confidence_score(self, round_data: Dict[str, Any], project_match: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence score for the funding round data."""
        score = 0.0
        
        # Project match score (40% weight)
        if project_match:
            score += project_match.get('similarity_score', 0) * 0.4
        
        # Amount presence and validity (20% weight)
        if round_data.get('amount_usd'):
            amount = round_data['amount_usd']
            if 1000 <= amount <= 10000000000:  # Reasonable range
                score += 0.2
            else:
                score += 0.1  # Partial credit for having amount
        
        # Round type presence (15% weight)
        if round_data.get('round_type'):
            score += 0.15
        
        # Investors presence (15% weight)
        investors = round_data.get('investors', [])
        if investors and len(investors) > 0:
            score += 0.15
        
        # Date presence (10% weight)
        if round_data.get('announced_at'):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _convert_to_usd(self, amount_str: str, unit: str, currency: str) -> Optional[float]:
        """Convert amount to USD."""
        try:
            # Clean amount string
            amount_clean = re.sub(r'[^0-9.]', '', amount_str)
            if not amount_clean:
                return None
            
            amount = float(amount_clean)
            
            # Apply unit multiplier
            if unit.lower() in ['million', 'm']:
                amount *= 1000000
            elif unit.lower() in ['billion', 'b']:
                amount *= 1000000000
            elif unit.lower() in ['thousand', 'k']:
                amount *= 1000
            
            # Apply currency conversion
            rate = self.currency_rates.get(currency.upper(), 1.0)
            amount_usd = amount * rate
            
            return amount_usd
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting amount to USD: {e}")
            return None
    
    def _parse_amount_string(self, amount_str: str, currency: str) -> Optional[float]:
        """Parse amount string like '$5M' or '5 million'."""
        try:
            # Extract number and unit
            pattern = r'([0-9,.]+)\s*(M|B|K|million|billion|thousand)?'
            match = re.search(pattern, amount_str, re.IGNORECASE)
            
            if not match:
                return None
            
            amount = match.group(1).replace(',', '')
            unit = match.group(2) or ''
            
            return self._convert_to_usd(amount, unit, currency)
            
        except Exception as e:
            logger.error(f"Error parsing amount string: {e}")
            return None
    
    def _normalize_round_type(self, round_type: str) -> str:
        """Normalize round type to standard format."""
        if not round_type:
            return ''
        
        round_type_clean = round_type.lower().strip()
        
        # Direct mapping
        if round_type_clean in self.round_type_mappings:
            return self.round_type_mappings[round_type_clean]
        
        # Pattern matching
        if 'pre' in round_type_clean and 'seed' in round_type_clean:
            return 'pre_seed'
        elif 'seed' in round_type_clean:
            return 'seed'
        elif 'series a' in round_type_clean or 'series-a' in round_type_clean:
            return 'series_a'
        elif 'series b' in round_type_clean or 'series-b' in round_type_clean:
            return 'series_b'
        elif 'series c' in round_type_clean or 'series-c' in round_type_clean:
            return 'series_c'
        elif 'bridge' in round_type_clean:
            return 'bridge'
        elif 'acquisition' in round_type_clean:
            return 'acquisition'
        
        return round_type_clean.replace(' ', '_').replace('-', '_')
    
    def _clean_company_name(self, company_name: str) -> str:
        """Clean company name by removing common suffixes."""
        if not company_name:
            return ''
        
        # Remove common company suffixes
        suffixes = ['Inc.', 'LLC', 'Corp', 'Corporation', 'Ltd', 'Limited', 'Co.', 'Company']
        
        cleaned = company_name.strip()
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # Remove "The" prefix
        if cleaned.startswith('The '):
            cleaned = cleaned[4:]
        
        return cleaned
    
    def _extract_date_from_context(self, text: str, source_url: str) -> Optional[datetime]:
        """Extract date from text context."""
        try:
            # Common date patterns
            date_patterns = [
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                r'Published on ([^\n]+)',
                r'Date: ([^\n]+)'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(0)
                        return dateutil.parser.parse(date_str)
                    except:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting date: {e}")
            return None
    
    def _extract_investors_from_context(self, text: str, source_url: str) -> List[str]:
        """Extract investor names from text context."""
        try:
            investors = []
            
            # Common investor patterns
            patterns = [
                r'led by ([^.]+)',
                r'backed by ([^.]+)',
                r'investors include ([^.]+)',
                r'participation from ([^.]+)',
                r'funded by ([^.]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    investor_text = match.group(1)
                    # Split by common separators
                    investor_names = re.split(r'[,;]|\sand\s|\s&\s', investor_text)
                    for name in investor_names:
                        name = name.strip()
                        if name and len(name) > 2:
                            investors.append(name)
            
            return list(set(investors))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting investors: {e}")
            return []
    
    def _parse_date(self, date_input: Any) -> Optional[datetime]:
        """Parse date from various input formats."""
        if not date_input:
            return None
        
        try:
            if isinstance(date_input, datetime):
                return date_input
            elif isinstance(date_input, str):
                return dateutil.parser.parse(date_input)
            else:
                return None
        except Exception as e:
            logger.error(f"Error parsing date: {e}")
            return None
    
    def _remove_duplicate_rounds(self, funding_rounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate funding rounds based on company name and amount."""
        seen = set()
        unique_rounds = []
        
        for round_data in funding_rounds:
            company_name = round_data.get('company_name', '').lower()
            amount = round_data.get('amount_usd', 0)
            
            # Create a unique key
            key = f"{company_name}_{amount}"
            
            if key not in seen:
                seen.add(key)
                unique_rounds.append(round_data)
        
        return unique_rounds
    
    async def upsert_funding_round(self, round_data: Dict[str, Any]) -> Optional[FundingRound]:
        """Upsert funding round into database."""
        try:
            project_match = round_data.get('project_match')
            project_id = None
            
            # Create or find project
            if project_match and project_match.get('similarity_score', 0) > 0.8:
                project_id = project_match['project_id']
            else:
                # Create new project
                project = await self._create_project_from_funding_data(round_data)
                if project:
                    project_id = project.id
            
            if not project_id:
                logger.warning(f"Could not determine project for funding round: {round_data.get('project_name')}")
                return None
            
            # Check if funding round already exists
            existing_query = select(FundingRound).where(
                FundingRound.project_id == project_id,
                FundingRound.round_type == round_data.get('round_type', ''),
                FundingRound.source_url == round_data.get('source_url', '')
            )
            
            result = await self.db.execute(existing_query)
            existing_round = result.scalar_one_or_none()
            
            if existing_round:
                # Update existing round
                existing_round.amount_usd = round_data.get('amount_usd')
                existing_round.announced_at = round_data.get('announced_at')
                existing_round.investors = round_data.get('investors', [])
                existing_round.meta_data = {
                    'confidence_score': round_data.get('confidence_score'),
                    'raw_data': round_data.get('raw_data')
                }
                funding_round = existing_round
            else:
                # Create new funding round
                funding_round = FundingRound(
                    project_id=project_id,
                    round_type=round_data.get('round_type', ''),
                    amount_usd=round_data.get('amount_usd'),
                    currency='USD',
                    announced_at=round_data.get('announced_at'),
                    investors=round_data.get('investors', []),
                    source_url=round_data.get('source_url', ''),
                    meta_data={
                        'confidence_score': round_data.get('confidence_score'),
                        'raw_data': round_data.get('raw_data')
                    }
                )
                
                self.db.add(funding_round)
            
            await self.db.commit()
            await self.db.refresh(funding_round)
            
            return funding_round
            
        except Exception as e:
            logger.error(f"Error upserting funding round: {e}")
            await self.db.rollback()
            return None
    
    async def _create_project_from_funding_data(self, round_data: Dict[str, Any]) -> Optional[Project]:
        """Create a new project from funding round data."""
        try:
            project_name = round_data.get('project_name', '').strip()
            if not project_name:
                return None
            
            # Generate slug
            slug = project_name.lower().replace(' ', '-').replace('.', '')
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            
            # Check if project with this slug already exists
            existing_query = select(Project).where(Project.slug == slug)
            result = await self.db.execute(existing_query)
            existing_project = result.scalar_one_or_none()
            
            if existing_project:
                return existing_project
            
            # Create new project
            project = Project(
                name=project_name,
                slug=slug,
                description=f"Project discovered from funding announcement",
                meta_data={
                    'discovered_from': 'funding_parser',
                    'source_url': round_data.get('source_url'),
                    'confidence_score': round_data.get('confidence_score')
                }
            )
            
            self.db.add(project)
            await self.db.commit()
            await self.db.refresh(project)
            
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await self.db.rollback()
            return None