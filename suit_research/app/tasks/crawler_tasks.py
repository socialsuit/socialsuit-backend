"""
Celery tasks for modular crawler operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from celery import current_task
from app.core.celery_app import celery_app
from app.core.mongodb import mongodb_client
from app.crawlers.base_fetcher import GenericFetcher, HTMLFetcher, RSSFetcher, JSONAPIFetcher
from app.crawlers.base_parser import GenericParser
from app.crawlers.normalizer import GenericNormalizer
from app.crawlers.vc_crawler import VCCrawler
from app.models.vc import Investor, FundingRound, VCCrawlJob

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def crawl_url_task(self, url: str, config: Optional[Dict[str, Any]] = None):
    """
    Main crawler task using modular framework.
    
    Args:
        url: URL to crawl
        config: Crawler configuration including:
            - fetcher_type: 'html', 'rss', 'json', or 'auto' (default)
            - requests_per_second: Rate limit (default: 1.0)
            - timeout: Request timeout (default: 30)
            - respect_robots: Whether to respect robots.txt (default: True)
            - user_agent: Custom user agent
    """
    config = config or {}
    
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Starting crawler', 'url': url, 'config': config}
        )
        
        # Run the async crawler
        result = asyncio.run(_run_modular_crawler(url, config))
        
        return {
            'status': 'completed',
            'url': url,
            'config': config,
            'raw_crawl_id': result.get('raw_crawl_id'),
            'structured_data': result.get('structured_data'),
            'stats': result.get('stats')
        }
        
    except Exception as exc:
        logger.error(f"Crawler task failed for {url}: {exc}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'url': url}
        )
        raise exc


async def _run_modular_crawler(url: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the modular crawler pipeline: Fetch -> Parse -> Normalize -> Store.
    """
    start_time = datetime.utcnow()
    
    try:
        # Initialize MongoDB connection
        await mongodb_client.init_mongodb()
        
        # Step 1: Fetch content
        logger.info(f"Fetching content from {url}")
        fetcher = _create_fetcher(config)
        fetch_result = await fetcher.fetch(url)
        
        if fetch_result.error:
            logger.error(f"Fetch failed for {url}: {fetch_result.error}")
            return {
                'error': fetch_result.error,
                'stats': {
                    'fetch_time': (datetime.utcnow() - start_time).total_seconds(),
                    'success': False
                }
            }
        
        # Step 2: Parse content
        logger.info(f"Parsing content from {url}")
        parser = GenericParser()
        parse_result = await parser.parse(fetch_result)
        
        if parse_result.error:
            logger.error(f"Parse failed for {url}: {parse_result.error}")
            return {
                'error': parse_result.error,
                'stats': {
                    'fetch_time': (datetime.utcnow() - start_time).total_seconds(),
                    'success': False
                }
            }
        
        # Step 3: Normalize data
        logger.info(f"Normalizing data from {url}")
        normalizer = GenericNormalizer()
        normalized_data = await normalizer.normalize(parse_result)
        
        # Step 4: Store in MongoDB
        logger.info(f"Storing data from {url}")
        storage_result = await _store_crawl_data(normalized_data)
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        # Update crawl statistics
        await _update_crawl_stats(url, True, total_time, len(fetch_result.content))
        
        logger.info(f"Successfully crawled {url} in {total_time:.2f} seconds")
        
        return {
            'raw_crawl_id': storage_result['raw_crawl_id'],
            'structured_data': normalized_data.structured_data,
            'stats': {
                'fetch_time': total_time,
                'content_length': len(fetch_result.content),
                'content_type': fetch_result.content_type,
                'status_code': fetch_result.status_code,
                'success': True
            }
        }
        
    except Exception as e:
        logger.error(f"Crawler pipeline failed for {url}: {e}")
        
        # Update failure statistics
        total_time = (datetime.utcnow() - start_time).total_seconds()
        await _update_crawl_stats(url, False, total_time, 0)
        
        raise e


def _create_fetcher(config: Dict[str, Any]):
    """Create appropriate fetcher based on configuration."""
    fetcher_type = config.get('fetcher_type', 'auto')
    
    fetcher_kwargs = {
        'requests_per_second': config.get('requests_per_second', 1.0),
        'timeout': config.get('timeout', 30),
        'respect_robots': config.get('respect_robots', True)
    }
    
    if config.get('user_agent'):
        fetcher_kwargs['user_agent'] = config['user_agent']
    
    if fetcher_type == 'html':
        return HTMLFetcher(**fetcher_kwargs)
    elif fetcher_type == 'rss':
        return RSSFetcher(**fetcher_kwargs)
    elif fetcher_type == 'json':
        return JSONAPIFetcher(**fetcher_kwargs)
    else:
        return GenericFetcher(**fetcher_kwargs)


async def _store_crawl_data(normalized_data: 'NormalizedData') -> Dict[str, Any]:
    """Store normalized data in MongoDB collections."""
    
    # Store raw crawl data
    raw_crawls_collection = mongodb_client.get_collection("raw_crawls")
    raw_crawl_doc = normalized_data.to_raw_crawl_document()
    raw_result = await raw_crawls_collection.insert_one(raw_crawl_doc)
    
    # Store structured data for further processing (optional)
    # This could be used for search indexing, analytics, etc.
    structured_collection = mongodb_client.get_collection("structured_content")
    structured_doc = normalized_data.to_structured_document()
    structured_doc['raw_crawl_id'] = raw_result.inserted_id
    await structured_collection.insert_one(structured_doc)
    
    return {
        'raw_crawl_id': str(raw_result.inserted_id),
        'structured_doc_created': True
    }


async def _update_crawl_stats(url: str, success: bool, duration: float, content_size: int):
    """Update crawl statistics in MongoDB."""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        today = datetime.utcnow().date()
        
        stats_collection = mongodb_client.get_collection("crawl_stats")
        
        # Update or create daily stats for this domain
        filter_doc = {"date": today, "source": domain}
        update_doc = {
            "$inc": {
                "total_crawls": 1,
                "successful_crawls": 1 if success else 0,
                "failed_crawls": 0 if success else 1,
                "total_data_size": content_size
            },
            "$push": {
                "response_times": duration
            },
            "$setOnInsert": {
                "date": today,
                "source": domain
            }
        }
        
        await stats_collection.update_one(
            filter_doc,
            update_doc,
            upsert=True
        )
        
        # Calculate average response time
        stats_doc = await stats_collection.find_one(filter_doc)
        if stats_doc and "response_times" in stats_doc:
            response_times = stats_doc["response_times"]
            avg_time = sum(response_times) / len(response_times)
            
            await stats_collection.update_one(
                filter_doc,
                {"$set": {"avg_response_time": avg_time}}
            )
        
    except Exception as e:
        logger.warning(f"Failed to update crawl stats: {e}")


@celery_app.task(bind=True)
def crawl_rss_feed_task(self, feed_url: str, config: Optional[Dict[str, Any]] = None):
    """
    Specialized task for crawling RSS feeds.
    """
    config = config or {}
    config['fetcher_type'] = 'rss'
    
    return crawl_url_task.apply_async(args=[feed_url, config])


@celery_app.task(bind=True)
def crawl_api_endpoint_task(self, api_url: str, config: Optional[Dict[str, Any]] = None):
    """
    Specialized task for crawling JSON APIs.
    """
    config = config or {}
    config['fetcher_type'] = 'json'
    
    return crawl_url_task.apply_async(args=[api_url, config])


@celery_app.task
def cleanup_old_crawler_data(days_to_keep: int = 30):
    """
    Clean up old crawler data.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Run cleanup in async context
        result = asyncio.run(_cleanup_old_data(cutoff_date))
        
        return {
            "status": "completed", 
            "message": f"Cleanup completed. Removed {result['removed_count']} old records.",
            "cutoff_date": cutoff_date.isoformat(),
            "removed_count": result['removed_count']
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


async def _cleanup_old_data(cutoff_date: datetime) -> Dict[str, Any]:
    """Clean up old data from MongoDB."""
    await mongodb_client.init_mongodb()
    
    # Clean up raw crawls
    raw_crawls_collection = mongodb_client.get_collection("raw_crawls")
    raw_result = await raw_crawls_collection.delete_many({
        "scraped_at": {"$lt": cutoff_date}
    })
    
    # Clean up structured content
    structured_collection = mongodb_client.get_collection("structured_content")
    structured_result = await structured_collection.delete_many({
        "normalized_at": {"$lt": cutoff_date}
    })
    
    # Clean up old crawl stats (keep aggregated daily stats)
    stats_collection = mongodb_client.get_collection("crawl_stats")
    stats_result = await stats_collection.delete_many({
        "date": {"$lt": cutoff_date.date()}
    })
    
    total_removed = (raw_result.deleted_count + 
                    structured_result.deleted_count + 
                    stats_result.deleted_count)
    
    logger.info(f"Cleanup removed {total_removed} old records")
    
    return {
        'removed_count': total_removed,
        'raw_crawls_removed': raw_result.deleted_count,
        'structured_content_removed': structured_result.deleted_count,
        'stats_removed': stats_result.deleted_count
    }


@celery_app.task
def health_check_crawler():
    """
    Health check task for crawler system.
    """
    try:
        # Test a simple crawl
        test_url = "https://httpbin.org/json"
        result = asyncio.run(_test_crawler_health(test_url))
        
        return {
            "status": "healthy",
            "test_url": test_url,
            "test_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Crawler health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def _test_crawler_health(test_url: str) -> Dict[str, Any]:
    """Test crawler health with a simple request."""
    fetcher = JSONAPIFetcher(requests_per_second=10.0, timeout=10)
    fetch_result = await fetcher.fetch(test_url)
    
    return {
        "success": fetch_result.error is None,
        "status_code": fetch_result.status_code,
        "content_length": len(fetch_result.content),
        "error": fetch_result.error
    }


# VC-specific crawler tasks

@celery_app.task(bind=True)
def crawl_vc_firm_task(self, vc_firm_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
    """
    Crawl a single VC firm's website for portfolio and funding data.
    
    Args:
        vc_firm_data: Dictionary containing VC firm info (name, website, investor_id)
        config: Crawler configuration
    """
    config = config or {}
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Starting VC crawl', 'vc_firm': vc_firm_data['name']}
        )
        
        # Run the VC crawler
        result = asyncio.run(_run_vc_crawler(vc_firm_data, config))
        
        return {
            'status': 'completed',
            'vc_firm': vc_firm_data['name'],
            'website': vc_firm_data['website'],
            'portfolio_companies_found': result.get('portfolio_companies_found', 0),
            'funding_rounds_found': result.get('funding_rounds_found', 0),
            'errors': result.get('errors', [])
        }
        
    except Exception as exc:
        logger.error(f"VC crawl task failed for {vc_firm_data['name']}: {exc}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'vc_firm': vc_firm_data['name']}
        )
        raise exc


@celery_app.task(bind=True)
def crawl_multiple_vc_firms_task(self, limit: int = 5, config: Optional[Dict[str, Any]] = None):
    """
    Crawl multiple VC firms from the database.
    
    Args:
        limit: Number of VC firms to crawl
        config: Crawler configuration
    """
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Starting batch VC crawl', 'limit': limit}
        )
        
        result = asyncio.run(_run_batch_vc_crawler(limit, config))
        
        return {
            'status': 'completed',
            'firms_processed': result.get('firms_processed', 0),
            'total_portfolio_companies': result.get('total_portfolio_companies', 0),
            'total_funding_rounds': result.get('total_funding_rounds', 0),
            'errors': result.get('errors', [])
        }
        
    except Exception as exc:
        logger.error(f"Batch VC crawl task failed: {exc}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise exc


async def _run_vc_crawler(vc_firm_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the VC crawler for a single firm.
    """
    start_time = datetime.utcnow()
    
    try:
        # Initialize MongoDB
        await mongodb_client.init_mongodb()
        
        # Create VC crawler
        vc_config = {
            'requests_per_second': config.get('requests_per_second', 0.5),  # Be respectful
            'timeout': config.get('timeout', 30),
            'respect_robots': config.get('respect_robots', True),
            'user_agent': config.get('user_agent', 'SuitResearch VC Crawler/1.0')
        }
        
        crawler = VCCrawler(**vc_config)
        
        # Crawl the VC site
        logger.info(f"Crawling VC firm: {vc_firm_data['name']}")
        crawl_result = await crawler.crawl_vc_site(vc_firm_data)
        
        # Store the results
        storage_result = await _store_vc_crawl_data(vc_firm_data, crawl_result)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"VC crawl completed for {vc_firm_data['name']} in {duration:.2f}s")
        
        return {
            'portfolio_companies_found': storage_result.get('portfolio_companies_stored', 0),
            'funding_rounds_found': storage_result.get('funding_rounds_stored', 0),
            'errors': crawl_result.get('errors', []),
            'duration': duration
        }
        
    except Exception as e:
        logger.error(f"VC crawler failed for {vc_firm_data['name']}: {e}")
        raise e


async def _run_batch_vc_crawler(limit: int, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run VC crawler for multiple firms.
    """
    try:
        # Get VC firms from seed script
        from scripts.seed_vcs import get_vc_firms_for_crawling
        
        vc_firms = await get_vc_firms_for_crawling(limit)
        
        if not vc_firms:
            logger.warning("No VC firms found for crawling")
            return {'firms_processed': 0, 'errors': ['No VC firms found']}
        
        results = {
            'firms_processed': 0,
            'total_portfolio_companies': 0,
            'total_funding_rounds': 0,
            'errors': []
        }
        
        for vc_firm in vc_firms:
            try:
                logger.info(f"Processing VC firm: {vc_firm['name']}")
                
                firm_result = await _run_vc_crawler(vc_firm, config or {})
                
                results['firms_processed'] += 1
                results['total_portfolio_companies'] += firm_result.get('portfolio_companies_found', 0)
                results['total_funding_rounds'] += firm_result.get('funding_rounds_found', 0)
                
                if firm_result.get('errors'):
                    results['errors'].extend(firm_result['errors'])
                
                # Add delay between firms to be respectful
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to process VC firm {vc_firm['name']}: {e}")
                results['errors'].append({
                    'vc_firm': vc_firm['name'],
                    'error': str(e)
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Batch VC crawler failed: {e}")
        raise e


async def _store_vc_crawl_data(vc_firm_data: Dict[str, Any], crawl_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store VC crawl results in MongoDB.
    """
    try:
        db = mongodb_client.get_database()
        
        portfolio_companies_stored = 0
        funding_rounds_stored = 0
        
        # Store portfolio companies
        if crawl_result.get('portfolio_data'):
            portfolio_data = crawl_result['portfolio_data']
            companies = portfolio_data.get('portfolio_companies', [])
            
            # Update investor record with portfolio companies
            if companies:
                investors_collection = db['investors']
                company_names = [comp['name'] for comp in companies if comp.get('name')]
                
                await investors_collection.update_one(
                    {'_id': vc_firm_data.get('investor_id')},
                    {
                        '$set': {
                            'portfolio_companies': company_names,
                            'crawled_at': datetime.utcnow()
                        },
                        '$addToSet': {
                            'source_urls': {
                                '$each': [url for url in crawl_result.get('source_urls', [])]
                            }
                        }
                    }
                )
                
                portfolio_companies_stored = len(companies)
                logger.info(f"Stored {portfolio_companies_stored} portfolio companies for {vc_firm_data['name']}")
        
        # Store funding rounds
        if crawl_result.get('press_data'):
            funding_rounds_collection = db['funding_rounds']
            
            for press_item in crawl_result['press_data']:
                funding_rounds = press_item.get('funding_rounds', [])
                
                for round_data in funding_rounds:
                    # Create FundingRound document
                    funding_round = FundingRound(
                        company_name=round_data.get('company_name', ''),
                        round_type=round_data.get('round_type', ''),
                        amount=round_data.get('amount'),
                        currency=round_data.get('currency', 'USD'),
                        participating_investors=[vc_firm_data['name']],
                        source_url=crawl_result.get('website', ''),
                        source_type='press_release',
                        extraction_method='vc_crawler'
                    )
                    
                    # Insert or update funding round
                    await funding_rounds_collection.insert_one(
                        funding_round.dict(by_alias=True)
                    )
                    
                    funding_rounds_stored += 1
            
            logger.info(f"Stored {funding_rounds_stored} funding rounds for {vc_firm_data['name']}")
        
        return {
            'portfolio_companies_stored': portfolio_companies_stored,
            'funding_rounds_stored': funding_rounds_stored
        }
        
    except Exception as e:
        logger.error(f"Failed to store VC crawl data: {e}")
        raise e


@celery_app.task
def cleanup_vc_data(days_to_keep: int = 90):
    """
    Clean up old VC crawl data.
    
    Args:
        days_to_keep: Number of days of data to keep
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        result = asyncio.run(_cleanup_old_vc_data(cutoff_date))
        
        logger.info(f"VC data cleanup completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"VC data cleanup failed: {exc}")
        raise exc


async def _cleanup_old_vc_data(cutoff_date: datetime) -> Dict[str, Any]:
    """
    Clean up old VC data from MongoDB.
    """
    try:
        await mongodb_client.init_mongodb()
        db = mongodb_client.get_database()
        
        # Clean up old funding rounds
        funding_rounds_result = await db['funding_rounds'].delete_many({
            'crawled_at': {'$lt': cutoff_date},
            'processed': False  # Only delete unprocessed staging data
        })
        
        # Clean up old crawl jobs
        crawl_jobs_result = await db['vc_crawl_jobs'].delete_many({
            'created_at': {'$lt': cutoff_date},
            'status': {'$in': ['completed', 'failed']}
        })
        
        return {
            'funding_rounds_deleted': funding_rounds_result.deleted_count,
            'crawl_jobs_deleted': crawl_jobs_result.deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"VC data cleanup failed: {e}")
        raise e


@celery_app.task(bind=True)
def start_crawler_task(self, crawler_config: Dict[str, Any]):
    """
    Start a crawler task with the given configuration.
    
    Args:
        crawler_config: Dictionary containing crawler configuration
                       including url, fetcher_type, rate limits, etc.
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Starting crawler', 'config': crawler_config}
        )
        
        url = crawler_config.get('url')
        if not url:
            raise ValueError("URL is required in crawler config")
        
        # Extract crawler configuration
        config = {
            'fetcher_type': crawler_config.get('fetcher_type', 'auto'),
            'requests_per_second': crawler_config.get('requests_per_second', 1.0),
            'timeout': crawler_config.get('timeout', 30),
            'respect_robots': crawler_config.get('respect_robots', True),
            'user_agent': crawler_config.get('user_agent')
        }
        
        # Run the crawler
        result = asyncio.run(_run_modular_crawler(url, config))
        
        return {
            'status': 'completed',
            'url': url,
            'config': config,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Crawler task failed: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'status': 'failed', 'error': str(e)}
        )
        raise e