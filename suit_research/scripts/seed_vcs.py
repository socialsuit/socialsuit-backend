#!/usr/bin/env python3
"""
Seed script for top 100 venture capital firms.
Populates the database with VC firm data for crawling.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from app.core.mongodb import mongodb_client
from app.models.vc import Investor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Top 100 VC firms with their websites and basic information
VC_FIRMS_DATA = [
    {
        "name": "Andreessen Horowitz",
        "website": "https://a16z.com",
        "description": "Venture capital firm investing in technology companies",
        "founded_year": 2009,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["fintech", "crypto", "ai", "enterprise", "consumer"],
        "geographies": ["united_states", "global"]
    },
    {
        "name": "Sequoia Capital",
        "website": "https://www.sequoiacap.com",
        "description": "Global venture capital firm partnering with bold founders",
        "founded_year": 1972,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["technology", "healthcare", "fintech", "enterprise"],
        "geographies": ["united_states", "china", "india", "southeast_asia"]
    },
    {
        "name": "Accel",
        "website": "https://www.accel.com",
        "description": "Early and growth-stage venture capital firm",
        "founded_year": 1983,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "healthcare"],
        "geographies": ["united_states", "europe", "india"]
    },
    {
        "name": "Kleiner Perkins",
        "website": "https://www.kleinerperkins.com",
        "description": "Venture capital firm investing in technology and life sciences",
        "founded_year": 1972,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "healthcare", "climate"],
        "geographies": ["united_states"]
    },
    {
        "name": "Benchmark",
        "website": "https://www.benchmark.com",
        "description": "Early-stage venture capital firm",
        "founded_year": 1995,
        "investment_stages": ["seed", "series_a", "series_b"],
        "sectors": ["enterprise", "consumer", "fintech", "marketplace"],
        "geographies": ["united_states"]
    },
    {
        "name": "Greylock Partners",
        "website": "https://greylock.com",
        "description": "Venture capital firm focused on early-stage companies",
        "founded_year": 1965,
        "investment_stages": ["seed", "series_a", "series_b"],
        "sectors": ["enterprise", "consumer", "ai", "cybersecurity"],
        "geographies": ["united_states"]
    },
    {
        "name": "General Catalyst",
        "website": "https://www.generalcatalyst.com",
        "description": "Venture capital firm investing across stages and geographies",
        "founded_year": 2000,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "healthcare"],
        "geographies": ["united_states", "europe"]
    },
    {
        "name": "Lightspeed Venture Partners",
        "website": "https://lsvp.com",
        "description": "Multi-stage venture capital firm",
        "founded_year": 2000,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "healthcare"],
        "geographies": ["united_states", "china", "india", "europe"]
    },
    {
        "name": "NEA (New Enterprise Associates)",
        "website": "https://www.nea.com",
        "description": "Global venture capital firm",
        "founded_year": 1977,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "healthcare", "energy"],
        "geographies": ["united_states", "asia", "europe"]
    },
    {
        "name": "Index Ventures",
        "website": "https://www.indexventures.com",
        "description": "International venture capital firm",
        "founded_year": 1996,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "gaming"],
        "geographies": ["europe", "united_states"]
    },
    {
        "name": "First Round Capital",
        "website": "https://firstround.com",
        "description": "Early-stage venture capital firm",
        "founded_year": 2004,
        "investment_stages": ["pre_seed", "seed", "series_a"],
        "sectors": ["enterprise", "consumer", "fintech", "marketplace"],
        "geographies": ["united_states"]
    },
    {
        "name": "Union Square Ventures",
        "website": "https://www.usv.com",
        "description": "Early-stage venture capital firm focused on network effects",
        "founded_year": 2003,
        "investment_stages": ["seed", "series_a", "series_b"],
        "sectors": ["consumer", "enterprise", "fintech", "crypto"],
        "geographies": ["united_states"]
    },
    {
        "name": "GV (Google Ventures)",
        "website": "https://www.gv.com",
        "description": "Venture capital arm of Alphabet Inc.",
        "founded_year": 2009,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "ai", "healthcare", "cybersecurity"],
        "geographies": ["united_states", "europe"]
    },
    {
        "name": "Insight Partners",
        "website": "https://www.insightpartners.com",
        "description": "Global software investor",
        "founded_year": 1995,
        "investment_stages": ["series_b", "series_c", "growth"],
        "sectors": ["enterprise", "fintech", "healthcare", "education"],
        "geographies": ["united_states", "europe"]
    },
    {
        "name": "Tiger Global Management",
        "website": "https://www.tigerglobal.com",
        "description": "Investment firm focused on private and public companies",
        "founded_year": 2001,
        "investment_stages": ["series_b", "series_c", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "e-commerce"],
        "geographies": ["united_states", "asia", "europe"]
    },
    {
        "name": "Coatue Management",
        "website": "https://www.coatue.com",
        "description": "Technology-focused investment firm",
        "founded_year": 1999,
        "investment_stages": ["series_b", "series_c", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "ai"],
        "geographies": ["united_states", "asia"]
    },
    {
        "name": "Bessemer Venture Partners",
        "website": "https://www.bvp.com",
        "description": "Global venture capital firm",
        "founded_year": 1911,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "healthcare"],
        "geographies": ["united_states", "europe", "india"]
    },
    {
        "name": "Founders Fund",
        "website": "https://foundersfund.com",
        "description": "Venture capital firm investing in transformative technologies",
        "founded_year": 2005,
        "investment_stages": ["seed", "series_a", "series_b", "growth"],
        "sectors": ["enterprise", "aerospace", "ai", "biotech"],
        "geographies": ["united_states"]
    },
    {
        "name": "Spark Capital",
        "website": "https://www.sparkcapital.com",
        "description": "Early-stage venture capital firm",
        "founded_year": 2005,
        "investment_stages": ["seed", "series_a", "series_b"],
        "sectors": ["enterprise", "consumer", "fintech", "marketplace"],
        "geographies": ["united_states"]
    },
    {
        "name": "Thrive Capital",
        "website": "https://thrivecap.com",
        "description": "Growth-stage venture capital firm",
        "founded_year": 2009,
        "investment_stages": ["series_a", "series_b", "growth"],
        "sectors": ["enterprise", "consumer", "fintech", "real_estate"],
        "geographies": ["united_states"]
    }
    # Note: This is a subset of 20 firms for demo purposes
    # In production, this would include all 100 firms
]


async def seed_vc_firms():
    """
    Seed the database with VC firm data.
    """
    try:
        # Initialize MongoDB connection
        await mongodb_client.init_mongodb()
        db = mongodb_client.get_database()
        collection = db["investors"]
        
        logger.info(f"Starting to seed {len(VC_FIRMS_DATA)} VC firms...")
        
        inserted_count = 0
        updated_count = 0
        
        for firm_data in VC_FIRMS_DATA:
            # Check if firm already exists
            existing_firm = await collection.find_one({"name": firm_data["name"]})
            
            if existing_firm:
                # Update existing firm
                firm_data["updated_at"] = datetime.utcnow()
                await collection.update_one(
                    {"_id": existing_firm["_id"]},
                    {"$set": firm_data}
                )
                updated_count += 1
                logger.info(f"Updated: {firm_data['name']}")
            else:
                # Create new investor record
                investor = Investor(**firm_data)
                await collection.insert_one(investor.dict(by_alias=True))
                inserted_count += 1
                logger.info(f"Inserted: {firm_data['name']}")
        
        logger.info(f"Seeding completed: {inserted_count} inserted, {updated_count} updated")
        return {"inserted": inserted_count, "updated": updated_count}
        
    except Exception as e:
        logger.error(f"Error seeding VC firms: {e}")
        raise e


async def get_vc_firms_for_crawling(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get VC firms from database for crawling.
    
    Args:
        limit: Number of firms to return for crawling
        
    Returns:
        List of VC firm data dictionaries
    """
    try:
        await mongodb_client.init_mongodb()
        db = mongodb_client.get_database()
        collection = db["investors"]
        
        # Get firms that haven't been crawled recently (or at all)
        cursor = collection.find(
            {"website": {"$exists": True, "$ne": None}}
        ).limit(limit)
        
        firms = []
        async for firm in cursor:
            firms.append({
                "name": firm["name"],
                "website": firm["website"],
                "investor_id": str(firm["_id"]),
                "sectors": firm.get("sectors", []),
                "investment_stages": firm.get("investment_stages", [])
            })
        
        logger.info(f"Retrieved {len(firms)} VC firms for crawling")
        return firms
        
    except Exception as e:
        logger.error(f"Error retrieving VC firms: {e}")
        raise e


async def main():
    """
    Main function to run the seeding process.
    """
    logger.info("Starting VC firms seeding process...")
    
    try:
        # Seed VC firms
        result = await seed_vc_firms()
        logger.info(f"Seeding result: {result}")
        
        # Test retrieval
        firms = await get_vc_firms_for_crawling(5)
        logger.info(f"Sample firms for crawling: {[f['name'] for f in firms]}")
        
        logger.info("VC firms seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Seeding process failed: {e}")
        raise e


if __name__ == "__main__":
    asyncio.run(main())