"""Specialized crawler for venture capital firms.
Extracts portfolio companies and funding information from VC websites."""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
import dateutil.parser

from .base_fetcher import GenericFetcher, FetchResult
from .base_parser import BaseParser, ParseResult
from .normalizer import BaseNormalizer, NormalizedData

logger = logging.getLogger(__name__)


class VCPortfolioParser(BaseParser):
    """Specialized parser for VC portfolio pages."""
    
    async def parse(self, fetch_result: FetchResult) -> ParseResult:
        """Parse VC portfolio page to extract portfolio companies."""
        try:
            soup = BeautifulSoup(fetch_result.content, 'html.parser')
            
            # Extract portfolio companies using various selectors
            portfolio_companies = self._extract_portfolio_companies(soup)
            
            # Extract page metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            
            structured_data = {
                "title": title,
                "description": description,
                "portfolio_companies": portfolio_companies,
                "page_type": "portfolio",
                "total_companies": len(portfolio_companies)
            }
            
            return ParseResult(
                url=fetch_result.url,
                data=structured_data,
                parser_type="VCPortfolioParser",
                parsed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Portfolio parsing failed: {e}")
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type="VCPortfolioParser",
                parsed_at=datetime.utcnow(),
                error=f"Portfolio parsing failed: {str(e)}"
            )
    
    def _extract_portfolio_companies(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract portfolio companies from various page structures."""
        companies = []
        
        # Common selectors for portfolio companies
        portfolio_selectors = [
            # Grid/card layouts
            '.portfolio-company', '.company-card', '.portfolio-item',
            '.company-item', '.investment-card', '.portfolio-grid-item',
            
            # List layouts
            '.company-list-item', '.portfolio-list-item',
            
            # Generic containers
            '[class*="portfolio"] [class*="company"]',
            '[class*="investment"] [class*="company"]',
            
            # Link-based
            'a[href*="portfolio"]', 'a[href*="company"]',
            
            # Table rows
            'tr[class*="company"]', 'tr[class*="portfolio"]'
        ]
        
        for selector in portfolio_selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} companies using selector: {selector}")
                for element in elements:
                    company = self._extract_company_info(element)
                    if company and company not in companies:
                        companies.append(company)
        
        # If no structured data found, try text-based extraction
        if not companies:
            companies = self._extract_companies_from_text(soup)
        
        return companies
    
    def _extract_company_info(self, element: Tag) -> Optional[Dict[str, Any]]:
        """Extract company information from a DOM element."""
        try:
            company = {}
            
            # Extract company name
            name_selectors = [
                '.company-name', '.name', 'h1', 'h2', 'h3', 'h4',
                '[class*="title"]', '[class*="name"]'
            ]
            
            name = None
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = self._clean_text(name_elem.get_text())
                    if name and len(name) > 2:
                        break
            
            # If no name found in child elements, use element text
            if not name:
                name = self._clean_text(element.get_text())
            
            if not name or len(name) < 2:
                return None
            
            company["name"] = name
            
            # Extract company URL
            link_elem = element.find('a', href=True)
            if link_elem:
                company["website"] = link_elem['href']
            
            # Extract description
            desc_selectors = ['.description', '.summary', '.bio', 'p']
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    desc = self._clean_text(desc_elem.get_text())
                    if desc and len(desc) > 10:
                        company["description"] = desc[:500]  # Limit length
                        break
            
            # Extract sector/industry
            sector_selectors = ['.sector', '.industry', '.category', '[class*="tag"]']
            for selector in sector_selectors:
                sector_elem = element.select_one(selector)
                if sector_elem:
                    sector = self._clean_text(sector_elem.get_text())
                    if sector:
                        company["sector"] = sector
                        break
            
            # Extract logo/image
            img_elem = element.find('img')
            if img_elem and img_elem.get('src'):
                company["logo_url"] = img_elem['src']
            
            return company
            
        except Exception as e:
            logger.warning(f"Error extracting company info: {e}")
            return None
    
    def _extract_companies_from_text(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract company names from text content when structured data isn't available."""
        companies = []
        
        # Look for text patterns that might indicate company names
        text_content = soup.get_text()
        
        # Common patterns for company listings
        patterns = [
            r'\b([A-Z][a-zA-Z0-9\s&.-]{2,30})\s*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.)\b',
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b',  # CamelCase names
        ]
        
        found_names = set()
        for pattern in patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                name = match.strip()
                if len(name) > 2 and name not in found_names:
                    found_names.add(name)
                    companies.append({"name": name})
        
        return companies[:50]  # Limit to prevent noise
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_elem = soup.find('title')
        if title_elem:
            return self._clean_text(title_elem.get_text())
        return "Portfolio Page"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        desc_elem = soup.find('meta', attrs={'name': 'description'})
        if desc_elem and desc_elem.get('content'):
            return self._clean_text(desc_elem['content'])
        return "VC Portfolio Companies"


class VCPressReleaseParser(BaseParser):
    """Specialized parser for VC press releases and news."""
    
    async def parse(self, fetch_result: FetchResult) -> ParseResult:
        """Parse press release to extract funding information."""
        try:
            soup = BeautifulSoup(fetch_result.content, 'html.parser')
            
            # Extract funding rounds from press release
            funding_rounds = self._extract_funding_rounds(soup)
            
            # Extract article metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            publish_date = self._extract_date(soup)
            
            structured_data = {
                "title": title,
                "description": description,
                "publish_date": publish_date,
                "funding_rounds": funding_rounds,
                "page_type": "press_release",
                "total_rounds": len(funding_rounds)
            }
            
            return ParseResult(
                url=fetch_result.url,
                data=structured_data,
                parser_type="VCPressReleaseParser",
                parsed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Press release parsing failed: {e}")
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type="VCPressReleaseParser",
                parsed_at=datetime.utcnow(),
                error=f"Press release parsing failed: {str(e)}"
            )
    
    def _extract_funding_rounds(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract funding round information from press release text."""
        funding_rounds = []
        text_content = soup.get_text()
        
        # Patterns for funding announcements
        funding_patterns = [
            # "Company X raises $Y million in Series A"
            r'([A-Z][a-zA-Z0-9\s&.-]+?)\s+(?:raises?|raised|secures?|secured|closes?|closed)\s+\$([0-9,.]+)\s*(million|billion)?\s*(?:in\s+)?(Series\s+[A-Z]|seed|pre-seed|Series\s+[A-Z][0-9]*)?',
            
            # "$Y million Series A for Company X"
            r'\$([0-9,.]+)\s*(million|billion)?\s*(Series\s+[A-Z]|seed|pre-seed)?\s*(?:for|in|to)\s+([A-Z][a-zA-Z0-9\s&.-]+)',
            
            # "Company X's $Y million Series A"
            r"([A-Z][a-zA-Z0-9\s&.-]+?)'s\s+\$([0-9,.]+)\s*(million|billion)?\s*(Series\s+[A-Z]|seed|pre-seed)?"
        ]
        
        for pattern in funding_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                funding_round = self._parse_funding_match(match, pattern)
                if funding_round:
                    funding_rounds.append(funding_round)
        
        # Remove duplicates based on company name
        seen_companies = set()
        unique_rounds = []
        for round_data in funding_rounds:
            company_name = round_data.get("company_name", "").lower()
            if company_name and company_name not in seen_companies:
                seen_companies.add(company_name)
                unique_rounds.append(round_data)
        
        return unique_rounds
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_elem = soup.find('title')
        if title_elem:
            return self._clean_text(title_elem.get_text())
        return "Press Release"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        desc_elem = soup.find('meta', attrs={'name': 'description'})
        if desc_elem and desc_elem.get('content'):
            return self._clean_text(desc_elem['content'])
        return "VC Press Release"
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date."""
        # Look for date in meta tags
        date_elem = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_elem and date_elem.get('content'):
            return date_elem['content']
        
        # Look for date in time elements
        time_elem = soup.find('time', attrs={'datetime': True})
        if time_elem:
            return time_elem['datetime']
        
        return None
    
    def _parse_funding_match(self, match, pattern: str) -> Optional[Dict[str, Any]]:
        """Parse a regex match into funding round data."""
        try:
            groups = match.groups()
            funding_round = {}
            
            # Different patterns have different group orders
            if "raises" in pattern or "secures" in pattern:
                # Pattern 1: Company raises $X million in Series A
                funding_round["company_name"] = groups[0].strip()
                amount_str = groups[1].replace(",", "")
                funding_round["amount_raw"] = amount_str
                
                # Convert to USD
                amount = float(amount_str)
                if groups[2] and "billion" in groups[2].lower():
                    amount *= 1000000000
                elif groups[2] and "million" in groups[2].lower():
                    amount *= 1000000
                funding_round["amount"] = amount
                
                if len(groups) > 3 and groups[3]:
                    funding_round["round_type"] = groups[3].lower().replace(" ", "_")
                    
            elif "for" in pattern or "to" in pattern:
                # Pattern 2: $X million for Company
                amount_str = groups[0].replace(",", "")
                funding_round["amount_raw"] = amount_str
                
                amount = float(amount_str)
                if groups[1] and "billion" in groups[1].lower():
                    amount *= 1000000000
                elif groups[1] and "million" in groups[1].lower():
                    amount *= 1000000
                funding_round["amount"] = amount
                
                if groups[2]:
                    funding_round["round_type"] = groups[2].lower().replace(" ", "_")
                
                funding_round["company_name"] = groups[3].strip()
            
            # Clean up company name
            company_name = funding_round.get("company_name", "")
            company_name = re.sub(r'\s+', ' ', company_name).strip()
            funding_round["company_name"] = company_name
            
            # Validate the extracted data
            if (funding_round.get("company_name") and 
                len(funding_round["company_name"]) > 1 and
                funding_round.get("amount", 0) > 0):
                return funding_round
            
            return None
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing funding match: {e}")
            return None


class VCNormalizer(BaseNormalizer):
    """Specialized normalizer for VC data."""
    
    async def normalize(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize VC-specific parsed data."""
        try:
            page_type = parse_result.data.get("page_type", "")
            if page_type == "portfolio":
                return await self._normalize_portfolio_data(parse_result)
            elif page_type == "press_release":
                return await self._normalize_press_release_data(parse_result)
            else:
                # Fallback to base normalization
                return await super().normalize(parse_result)
                
        except Exception as e:
            logger.error(f"VC normalization failed: {e}")
            return NormalizedData(
                raw_crawl_data={"url": parse_result.url, "error": f"Normalization failed: {str(e)}"},
                content_type="vc_data"
            )
    
    async def _normalize_portfolio_data(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize portfolio page data."""
        structured_data = parse_result.data
        
        # Extract portfolio companies
        portfolio_companies = structured_data.get("portfolio_companies", [])
        
        # Normalize company data
        normalized_companies = []
        for company in portfolio_companies:
            normalized_company = {
                "name": self._clean_text(company.get("name", "")),
                "website": self._normalize_url(company.get("website")),
                "description": self._clean_text(company.get("description", "")),
                "sector": self._clean_text(company.get("sector", "")),
                "logo_url": self._normalize_url(company.get("logo_url"))
            }
            
            # Only include companies with valid names
            if normalized_company["name"] and len(normalized_company["name"]) > 1:
                normalized_companies.append(normalized_company)
        
        return NormalizedData(
            raw_crawl_data={
                "url": parse_result.url,
                "parser_type": "VCPortfolioParser",
                "fetch_time": parse_result.parsed_at
            },
            structured_data={
                "title": self._clean_text(structured_data.get("title", "")),
                "description": self._clean_text(structured_data.get("description", "")),
                "portfolio_companies": normalized_companies,
                "total_companies": len(normalized_companies),
                "page_type": "portfolio",
                "category": "venture_capital",
                "domain": self._extract_domain(parse_result.url)
            },
            content_type="vc_portfolio"
        )
    
    async def _normalize_press_release_data(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize press release data."""
        structured_data = parse_result.data
        
        # Extract and normalize funding rounds
        funding_rounds = structured_data.get("funding_rounds", [])
        normalized_rounds = []
        
        for round_data in funding_rounds:
            normalized_round = {
                "company_name": self._clean_text(round_data.get("company_name", "")),
                "amount": round_data.get("amount"),
                "amount_raw": round_data.get("amount_raw", ""),
                "round_type": round_data.get("round_type", ""),
                "currency": "USD"  # Assuming USD for now
            }
            
            if normalized_round["company_name"] and normalized_round["amount"]:
                normalized_rounds.append(normalized_round)
        
        return NormalizedData(
            raw_crawl_data={
                "url": parse_result.url,
                "parser_type": "VCPressReleaseParser",
                "fetch_time": parse_result.parsed_at
            },
            structured_data={
                "title": self._clean_text(structured_data.get("title", "")),
                "description": self._clean_text(structured_data.get("description", "")),
                "funding_rounds": normalized_rounds,
                "total_rounds": len(normalized_rounds),
                "page_type": "press_release",
                "publish_date": structured_data.get("publish_date"),
                "category": "venture_capital",
                "domain": self._extract_domain(parse_result.url)
            },
            content_type="vc_press_release"
        )


class VCCrawler:
    """Main VC crawler that orchestrates fetching, parsing, and normalization."""
    
    def __init__(self, **config):
        self.config = config
        self.fetcher = GenericFetcher(**config)
        self.portfolio_parser = VCPortfolioParser()
        self.press_parser = VCPressReleaseParser()
        self.normalizer = VCNormalizer()
    
    async def crawl_vc_site(self, vc_firm: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl a VC firm's website for portfolio and press information."""
        results = {
            "vc_firm": vc_firm["name"],
            "website": vc_firm["website"],
            "portfolio_data": None,
            "press_data": [],
            "errors": []
        }
        
        try:
            # Discover URLs to crawl
            urls_to_crawl = await self._discover_urls(vc_firm["website"])
            
            for url_info in urls_to_crawl:
                try:
                    # Fetch the page
                    fetch_result = await self.fetcher.fetch(url_info["url"])
                    
                    if fetch_result.error:
                        results["errors"].append({
                            "url": url_info["url"],
                            "error": fetch_result.error
                        })
                        continue
                    
                    # Parse based on page type
                    if url_info["type"] == "portfolio":
                        parse_result = await self.portfolio_parser.parse(fetch_result)
                        if not parse_result.error:
                            normalized_data = await self.normalizer.normalize(parse_result)
                            results["portfolio_data"] = normalized_data.structured_data
                    
                    elif url_info["type"] == "press":
                        parse_result = await self.press_parser.parse(fetch_result)
                        if not parse_result.error:
                            normalized_data = await self.normalizer.normalize(parse_result)
                            results["press_data"].append(normalized_data.structured_data)
                    
                except Exception as e:
                    results["errors"].append({
                        "url": url_info["url"],
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"VC crawling failed for {vc_firm['name']}: {e}")
            results["errors"].append({"general_error": str(e)})
            return results
    
    async def _discover_urls(self, base_url: str) -> List[Dict[str, str]]:
        """Discover relevant URLs to crawl from the VC website."""
        urls = []
        
        try:
            # Fetch the main page to discover links
            fetch_result = await self.fetcher.fetch(base_url)
            
            if fetch_result.error:
                logger.warning(f"Could not fetch main page {base_url}: {fetch_result.error}")
                return urls
            
            soup = BeautifulSoup(fetch_result.content, 'html.parser')
            
            # Look for portfolio-related links
            portfolio_keywords = ['portfolio', 'companies', 'investments', 'startups']
            press_keywords = ['news', 'press', 'blog', 'announcements', 'media']
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                link_text = link.get_text().lower()
                
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                
                # Check if it's a portfolio page
                if any(keyword in link_text or keyword in href.lower() for keyword in portfolio_keywords):
                    urls.append({"url": full_url, "type": "portfolio"})
                
                # Check if it's a press/news page
                elif any(keyword in link_text or keyword in href.lower() for keyword in press_keywords):
                    urls.append({"url": full_url, "type": "press"})
            
            # Remove duplicates
            seen_urls = set()
            unique_urls = []
            for url_info in urls:
                if url_info["url"] not in seen_urls:
                    seen_urls.add(url_info["url"])
                    unique_urls.append(url_info)
            
            logger.info(f"Discovered {len(unique_urls)} URLs for {base_url}")
            return unique_urls[:10]  # Limit to prevent excessive crawling
            
        except Exception as e:
            logger.error(f"URL discovery failed for {base_url}: {e}")
            return urls