# Models package

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .research import Research, ResearchCategory
from .project import Project
from .funding import FundingRound
from .investor import Investor, InvestorPortfolio
from .api import ApiKey, Webhook
from .alert import Alert, Watchlist
from .crawl import RawCrawl, CrawlStats

# Export all models
__all__ = [
    "User",
    "Research", 
    "ResearchCategory",
    "Project",
    "FundingRound", 
    "Investor",
    "InvestorPortfolio",
    "ApiKey",
    "Webhook",
    "Alert",
    "Watchlist",
    "RawCrawl",
    "CrawlStats"
]