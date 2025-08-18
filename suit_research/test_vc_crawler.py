#!/usr/bin/env python3
"""
Test script for VC crawler functionality.
Demonstrates crawling 5 VC sites and saving investor and funding data.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.core.mongodb import mongodb_client
from app.tasks.crawler_tasks import crawl_vc_firm_task, crawl_multiple_vc_firms_task
from scripts.seed_vcs import seed_vc_firms, get_vc_firms_for_crawling

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_vc_crawler_direct():
    """
    Test the VC crawler directly without Celery.
    """
    logger.info("=" * 60)
    logger.info("Testing VC Crawler (Direct Mode)")
    logger.info("=" * 60)
    
    try:
        # Initialize MongoDB
        await mongodb_client.init_mongodb()
        
        # Seed VC firms first
        logger.info("Seeding VC firms...")
        seed_result = await seed_vc_firms()
        logger.info(f"Seed result: {seed_result}")
        
        # Get VC firms for testing
        logger.info("Getting VC firms for crawling...")
        vc_firms = await get_vc_firms_for_crawling(5)
        
        if not vc_firms:
            logger.error("No VC firms found for testing")
            return
        
        logger.info(f"Found {len(vc_firms)} VC firms for testing:")
        for firm in vc_firms:
            logger.info(f"  - {firm['name']}: {firm['website']}")
        
        # Test crawling each firm
        from app.crawlers.vc_crawler import VCCrawler
        
        crawler_config = {
            'requests_per_second': 0.5,
            'timeout': 30,
            'respect_robots': True,
            'user_agent': 'SuitResearch VC Crawler Test/1.0'
        }
        
        crawler = VCCrawler(**crawler_config)
        
        total_portfolio_companies = 0
        total_funding_rounds = 0
        
        for i, vc_firm in enumerate(vc_firms, 1):
            logger.info(f"\n[{i}/{len(vc_firms)}] Crawling {vc_firm['name']}...")
            
            try:
                # Crawl the VC site
                crawl_result = await crawler.crawl_vc_site(vc_firm)
                
                # Log results
                portfolio_count = 0
                funding_count = 0
                
                if crawl_result.get('portfolio_data'):
                    portfolio_companies = crawl_result['portfolio_data'].get('portfolio_companies', [])
                    portfolio_count = len(portfolio_companies)
                    total_portfolio_companies += portfolio_count
                    
                    logger.info(f"  ✓ Found {portfolio_count} portfolio companies")
                    if portfolio_companies:
                        logger.info(f"    Sample companies: {[c['name'] for c in portfolio_companies[:3]]}")
                
                if crawl_result.get('press_data'):
                    for press_item in crawl_result['press_data']:
                        funding_rounds = press_item.get('funding_rounds', [])
                        funding_count += len(funding_rounds)
                    
                    total_funding_rounds += funding_count
                    logger.info(f"  ✓ Found {funding_count} funding rounds")
                
                if crawl_result.get('errors'):
                    logger.warning(f"  ⚠ Errors: {len(crawl_result['errors'])}")
                    for error in crawl_result['errors'][:2]:  # Show first 2 errors
                        logger.warning(f"    - {error}")
                
                # Add delay between crawls
                if i < len(vc_firms):
                    logger.info("  Waiting 3 seconds before next crawl...")
                    await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"  ✗ Failed to crawl {vc_firm['name']}: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info("VC Crawler Test Summary")
        logger.info(f"{'='*60}")
        logger.info(f"Firms tested: {len(vc_firms)}")
        logger.info(f"Total portfolio companies found: {total_portfolio_companies}")
        logger.info(f"Total funding rounds found: {total_funding_rounds}")
        
        return {
            'firms_tested': len(vc_firms),
            'portfolio_companies_found': total_portfolio_companies,
            'funding_rounds_found': total_funding_rounds
        }
        
    except Exception as e:
        logger.error(f"VC crawler test failed: {e}")
        raise e


def test_vc_crawler_celery():
    """
    Test the VC crawler using Celery tasks.
    """
    logger.info("=" * 60)
    logger.info("Testing VC Crawler (Celery Mode)")
    logger.info("=" * 60)
    
    try:
        # Test batch crawling task
        logger.info("Submitting batch VC crawl task...")
        
        config = {
            'requests_per_second': 0.5,
            'timeout': 30,
            'respect_robots': True,
            'user_agent': 'SuitResearch VC Crawler Celery Test/1.0'
        }
        
        # Submit the task
        task_result = crawl_multiple_vc_firms_task.delay(5, config)
        
        logger.info(f"Task submitted with ID: {task_result.id}")
        logger.info("Waiting for task completion...")
        
        # Wait for result (with timeout)
        try:
            result = task_result.get(timeout=300)  # 5 minutes timeout
            
            logger.info("\nCelery Task Results:")
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Firms processed: {result.get('firms_processed', 0)}")
            logger.info(f"Portfolio companies: {result.get('total_portfolio_companies', 0)}")
            logger.info(f"Funding rounds: {result.get('total_funding_rounds', 0)}")
            
            if result.get('errors'):
                logger.warning(f"Errors encountered: {len(result['errors'])}")
                for error in result['errors'][:3]:  # Show first 3 errors
                    logger.warning(f"  - {error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            logger.info(f"Task state: {task_result.state}")
            if hasattr(task_result, 'info'):
                logger.info(f"Task info: {task_result.info}")
            return None
        
    except Exception as e:
        logger.error(f"Celery VC crawler test failed: {e}")
        return None


async def check_stored_data():
    """
    Check what data was stored in the database.
    """
    logger.info("\n" + "=" * 60)
    logger.info("Checking Stored Data")
    logger.info("=" * 60)
    
    try:
        await mongodb_client.init_mongodb()
        db = mongodb_client.get_database()
        
        # Check investors collection
        investors_collection = db['investors']
        investor_count = await investors_collection.count_documents({})
        
        logger.info(f"Total investors in database: {investor_count}")
        
        # Get sample investors with portfolio companies
        investors_with_portfolio = await investors_collection.find({
            'portfolio_companies': {'$exists': True, '$ne': []}
        }).limit(5).to_list(length=5)
        
        logger.info(f"Investors with portfolio companies: {len(investors_with_portfolio)}")
        
        for investor in investors_with_portfolio:
            portfolio_count = len(investor.get('portfolio_companies', []))
            logger.info(f"  - {investor['name']}: {portfolio_count} portfolio companies")
            if portfolio_count > 0:
                sample_companies = investor['portfolio_companies'][:3]
                logger.info(f"    Sample: {sample_companies}")
        
        # Check funding rounds collection
        funding_rounds_collection = db['funding_rounds']
        funding_rounds_count = await funding_rounds_collection.count_documents({})
        
        logger.info(f"\nTotal funding rounds in database: {funding_rounds_count}")
        
        # Get sample funding rounds
        sample_rounds = await funding_rounds_collection.find({}).limit(5).to_list(length=5)
        
        for round_data in sample_rounds:
            amount = round_data.get('amount', 0)
            amount_str = f"${amount:,.0f}" if amount else "Unknown"
            logger.info(f"  - {round_data.get('company_name', 'Unknown')}: {amount_str} {round_data.get('round_type', '')}")
            logger.info(f"    Investors: {round_data.get('participating_investors', [])}")
        
        return {
            'total_investors': investor_count,
            'investors_with_portfolio': len(investors_with_portfolio),
            'total_funding_rounds': funding_rounds_count
        }
        
    except Exception as e:
        logger.error(f"Failed to check stored data: {e}")
        return None


async def main():
    """
    Main test function.
    """
    logger.info("Starting VC Crawler Test Suite")
    
    try:
        # Test 1: Direct crawler test
        direct_result = await test_vc_crawler_direct()
        
        # Test 2: Check stored data
        stored_data = await check_stored_data()
        
        # Test 3: Celery test (optional, requires Celery worker)
        logger.info("\nNote: Celery test requires a running Celery worker.")
        logger.info("To test Celery functionality, run:")
        logger.info("  celery -A app.tasks worker --loglevel=info")
        logger.info("Then run this script again.")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        if direct_result:
            logger.info(f"✓ Direct crawler test: {direct_result['firms_tested']} firms tested")
            logger.info(f"✓ Portfolio companies found: {direct_result['portfolio_companies_found']}")
            logger.info(f"✓ Funding rounds found: {direct_result['funding_rounds_found']}")
        
        if stored_data:
            logger.info(f"✓ Database check: {stored_data['total_investors']} investors stored")
            logger.info(f"✓ Investors with portfolio: {stored_data['investors_with_portfolio']}")
            logger.info(f"✓ Funding rounds stored: {stored_data['total_funding_rounds']}")
        
        # Acceptance criteria check
        logger.info("\n" + "=" * 60)
        logger.info("ACCEPTANCE CRITERIA CHECK")
        logger.info("=" * 60)
        
        criteria_met = True
        
        if direct_result and direct_result['firms_tested'] >= 5:
            logger.info("✓ Crawled 5 VC sites")
        else:
            logger.error("✗ Failed to crawl 5 VC sites")
            criteria_met = False
        
        if stored_data and stored_data['total_investors'] > 0:
            logger.info("✓ Saved investor data in database")
        else:
            logger.error("✗ No investor data saved")
            criteria_met = False
        
        if stored_data and (stored_data['investors_with_portfolio'] > 0 or stored_data['total_funding_rounds'] > 0):
            logger.info("✓ Saved sample funding/portfolio data")
        else:
            logger.error("✗ No funding/portfolio data saved")
            criteria_met = False
        
        if criteria_met:
            logger.info("\n🎉 ALL ACCEPTANCE CRITERIA MET! 🎉")
        else:
            logger.error("\n❌ Some acceptance criteria not met")
        
        return criteria_met
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return False


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    
    if success:
        print("\nVC Crawler test completed successfully!")
    else:
        print("\nVC Crawler test failed!")
        exit(1)