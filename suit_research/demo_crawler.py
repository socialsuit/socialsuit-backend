#!/usr/bin/env python3
"""
Demo script for testing the modular crawler framework.

This script demonstrates how to use the crawler framework to fetch,
parse, and store content from various sources.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_crawler_framework():
    """
    Demonstrate the modular crawler framework with various content types.
    """
    from app.core.mongodb import mongodb_client
    from app.crawlers.base_fetcher import GenericFetcher, RSSFetcher, JSONAPIFetcher
    from app.crawlers.base_parser import GenericParser
    from app.crawlers.normalizer import GenericNormalizer
    
    # Initialize MongoDB
    await mongodb_client.init_mongodb()
    logger.info("MongoDB connection initialized")
    
    # Test URLs for different content types
    test_urls = {
        "rss": "https://techcrunch.com/feed/",
        "json": "https://httpbin.org/json",
        "html": "https://httpbin.org/html"
    }
    
    results = {}
    
    for content_type, url in test_urls.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {content_type.upper()} crawler for: {url}")
        logger.info(f"{'='*50}")
        
        try:
            # Step 1: Fetch content
            logger.info("Step 1: Fetching content...")
            if content_type == "rss":
                fetcher = RSSFetcher(requests_per_second=2.0, timeout=15)
            elif content_type == "json":
                fetcher = JSONAPIFetcher(requests_per_second=2.0, timeout=15)
            else:
                fetcher = GenericFetcher(requests_per_second=2.0, timeout=15)
            
            fetch_result = await fetcher.fetch(url)
            
            if fetch_result.error:
                logger.error(f"Fetch failed: {fetch_result.error}")
                results[content_type] = {"error": fetch_result.error}
                continue
            
            logger.info(f"✓ Fetched {len(fetch_result.content)} bytes")
            logger.info(f"  Content-Type: {fetch_result.content_type}")
            logger.info(f"  Status Code: {fetch_result.status_code}")
            
            # Step 2: Parse content
            logger.info("Step 2: Parsing content...")
            parser = GenericParser()
            parse_result = await parser.parse(fetch_result)
            
            if parse_result.error:
                logger.error(f"Parse failed: {parse_result.error}")
                results[content_type] = {"error": parse_result.error}
                continue
            
            logger.info(f"✓ Parsed content successfully")
            logger.info(f"  Title: {parse_result.structured_data.get('title', 'N/A')[:50]}...")
            logger.info(f"  Content Type: {parse_result.content_type}")
            
            # Step 3: Normalize data
            logger.info("Step 3: Normalizing data...")
            normalizer = GenericNormalizer()
            normalized_data = await normalizer.normalize(parse_result)
            
            logger.info(f"✓ Normalized data successfully")
            logger.info(f"  Source: {normalized_data.source}")
            logger.info(f"  Domain: {normalized_data.domain}")
            logger.info(f"  Category: {normalized_data.category}")
            
            # Step 4: Store in MongoDB
            logger.info("Step 4: Storing in MongoDB...")
            
            # Store raw crawl data
            raw_crawls_collection = mongodb_client.get_collection("raw_crawls")
            raw_crawl_doc = normalized_data.to_raw_crawl_document()
            raw_result = await raw_crawls_collection.insert_one(raw_crawl_doc)
            
            # Store structured data
            structured_collection = mongodb_client.get_collection("structured_content")
            structured_doc = normalized_data.to_structured_document()
            structured_doc['raw_crawl_id'] = raw_result.inserted_id
            structured_result = await structured_collection.insert_one(structured_doc)
            
            logger.info(f"✓ Stored in MongoDB")
            logger.info(f"  Raw Crawl ID: {raw_result.inserted_id}")
            logger.info(f"  Structured Doc ID: {structured_result.inserted_id}")
            
            results[content_type] = {
                "success": True,
                "raw_crawl_id": str(raw_result.inserted_id),
                "structured_doc_id": str(structured_result.inserted_id),
                "content_length": len(fetch_result.content),
                "title": normalized_data.structured_data.get('title', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Demo failed for {content_type}: {e}")
            results[content_type] = {"error": str(e)}
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("DEMO SUMMARY")
    logger.info(f"{'='*50}")
    
    for content_type, result in results.items():
        if result.get("success"):
            logger.info(f"✓ {content_type.upper()}: SUCCESS")
            logger.info(f"  Title: {result.get('title', 'N/A')[:50]}...")
            logger.info(f"  Raw Crawl ID: {result.get('raw_crawl_id')}")
        else:
            logger.error(f"✗ {content_type.upper()}: FAILED - {result.get('error')}")
    
    return results

async def demo_celery_task():
    """
    Demonstrate using the Celery task directly.
    """
    logger.info(f"\n{'='*50}")
    logger.info("TESTING CELERY TASK")
    logger.info(f"{'='*50}")
    
    try:
        from app.tasks.crawler_tasks import crawl_url_task
        from configs.techcrunch_rss_config import get_techcrunch_config
        
        # Get TechCrunch config
        config = get_techcrunch_config("main")
        
        logger.info(f"Submitting Celery task for: {config['url']}")
        
        # Submit task (this would normally be async, but for demo we'll run sync)
        import asyncio
        from app.tasks.crawler_tasks import _run_modular_crawler
        
        result = await _run_modular_crawler(config['url'], config['config'])
        
        logger.info("✓ Celery task completed successfully")
        logger.info(f"  Raw Crawl ID: {result.get('raw_crawl_id')}")
        logger.info(f"  Content Length: {result.get('stats', {}).get('content_length', 0)} bytes")
        
        return result
        
    except Exception as e:
        logger.error(f"Celery task demo failed: {e}")
        return {"error": str(e)}

async def check_mongodb_data():
    """
    Check what data was stored in MongoDB.
    """
    logger.info(f"\n{'='*50}")
    logger.info("CHECKING MONGODB DATA")
    logger.info(f"{'='*50}")
    
    try:
        from app.core.mongodb import mongodb_client
        
        # Check raw crawls
        raw_crawls_collection = mongodb_client.get_collection("raw_crawls")
        raw_count = await raw_crawls_collection.count_documents({})
        logger.info(f"Raw crawls in database: {raw_count}")
        
        # Get latest raw crawl
        latest_raw = await raw_crawls_collection.find_one(
            {}, sort=[("scraped_at", -1)]
        )
        if latest_raw:
            logger.info(f"Latest raw crawl:")
            logger.info(f"  ID: {latest_raw['_id']}")
            logger.info(f"  Source: {latest_raw.get('source', 'N/A')}")
            logger.info(f"  Content Type: {latest_raw.get('content_type', 'N/A')}")
            logger.info(f"  Scraped At: {latest_raw.get('scraped_at', 'N/A')}")
        
        # Check structured content
        structured_collection = mongodb_client.get_collection("structured_content")
        structured_count = await structured_collection.count_documents({})
        logger.info(f"Structured documents in database: {structured_count}")
        
        # Get latest structured content
        latest_structured = await structured_collection.find_one(
            {}, sort=[("normalized_at", -1)]
        )
        if latest_structured:
            logger.info(f"Latest structured content:")
            logger.info(f"  ID: {latest_structured['_id']}")
            logger.info(f"  Title: {latest_structured.get('title', 'N/A')[:50]}...")
            logger.info(f"  Domain: {latest_structured.get('domain', 'N/A')}")
            logger.info(f"  Category: {latest_structured.get('category', 'N/A')}")
        
    except Exception as e:
        logger.error(f"MongoDB check failed: {e}")

async def main():
    """
    Main demo function.
    """
    logger.info("Starting Modular Crawler Framework Demo")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        # Demo 1: Test the modular framework directly
        await demo_crawler_framework()
        
        # Demo 2: Test Celery task
        await demo_celery_task()
        
        # Demo 3: Check MongoDB data
        await check_mongodb_data()
        
        logger.info(f"\n{'='*50}")
        logger.info("DEMO COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*50}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())