#!/usr/bin/env python3
"""
Test script for Celery crawler tasks.

This script tests the Celery worker functionality by submitting
crawler tasks and monitoring their execution.
"""

import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_celery_crawler():
    """
    Test the Celery crawler tasks.
    """
    logger.info("Testing Celery Crawler Tasks")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        # Import Celery tasks
        from app.tasks.crawler_tasks import crawl_url_task, crawl_rss_feed_task
        from configs.techcrunch_rss_config import get_techcrunch_config
        
        # Test 1: Simple URL crawl
        logger.info("\n" + "="*50)
        logger.info("TEST 1: Simple URL Crawl")
        logger.info("="*50)
        
        test_url = "https://httpbin.org/json"
        config = {
            "fetcher_type": "json",
            "requests_per_second": 2.0,
            "timeout": 15,
            "respect_robots": True
        }
        
        logger.info(f"Submitting task for: {test_url}")
        task1 = crawl_url_task.delay(test_url, config)
        logger.info(f"Task ID: {task1.id}")
        logger.info(f"Task State: {task1.state}")
        
        # Wait for completion
        logger.info("Waiting for task completion...")
        result1 = task1.get(timeout=60)  # Wait up to 60 seconds
        
        logger.info("✓ Task completed successfully!")
        logger.info(f"Result: {result1}")
        
        # Test 2: TechCrunch RSS feed
        logger.info("\n" + "="*50)
        logger.info("TEST 2: TechCrunch RSS Feed")
        logger.info("="*50)
        
        tc_config = get_techcrunch_config("main")
        
        logger.info(f"Submitting RSS task for: {tc_config['url']}")
        task2 = crawl_rss_feed_task.delay(tc_config['url'], tc_config['config'])
        logger.info(f"Task ID: {task2.id}")
        logger.info(f"Task State: {task2.state}")
        
        # Wait for completion
        logger.info("Waiting for RSS task completion...")
        result2 = task2.get(timeout=120)  # Wait up to 2 minutes
        
        logger.info("✓ RSS Task completed successfully!")
        logger.info(f"Result: {result2}")
        
        # Test 3: Health check
        logger.info("\n" + "="*50)
        logger.info("TEST 3: Crawler Health Check")
        logger.info("="*50)
        
        from app.tasks.crawler_tasks import health_check_crawler
        
        logger.info("Running health check...")
        task3 = health_check_crawler.delay()
        result3 = task3.get(timeout=30)
        
        logger.info("✓ Health check completed!")
        logger.info(f"Health Status: {result3.get('status', 'unknown')}")
        logger.info(f"Result: {result3}")
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        logger.info("✓ All Celery crawler tests passed!")
        logger.info(f"✓ Simple URL crawl: {result1.get('status', 'unknown')}")
        logger.info(f"✓ RSS feed crawl: {result2.get('status', 'unknown')}")
        logger.info(f"✓ Health check: {result3.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Celery test failed: {e}")
        return False

def test_task_monitoring():
    """
    Test task monitoring and status checking.
    """
    logger.info("\n" + "="*50)
    logger.info("TASK MONITORING TEST")
    logger.info("="*50)
    
    try:
        from app.tasks.crawler_tasks import crawl_url_task
        
        # Submit a task
        test_url = "https://httpbin.org/html"
        config = {"fetcher_type": "html", "timeout": 20}
        
        logger.info(f"Submitting monitored task for: {test_url}")
        task = crawl_url_task.delay(test_url, config)
        
        # Monitor task progress
        logger.info(f"Task ID: {task.id}")
        
        while not task.ready():
            logger.info(f"Task state: {task.state}")
            if task.state == 'PROGRESS':
                logger.info(f"Progress info: {task.info}")
            time.sleep(2)
        
        if task.successful():
            result = task.result
            logger.info("✓ Monitored task completed successfully!")
            logger.info(f"Final result: {result}")
        else:
            logger.error(f"✗ Task failed: {task.info}")
            
    except Exception as e:
        logger.error(f"Task monitoring test failed: {e}")

def check_celery_connection():
    """
    Check if Celery broker is accessible.
    """
    logger.info("\n" + "="*50)
    logger.info("CELERY CONNECTION TEST")
    logger.info("="*50)
    
    try:
        from app.core.celery_app import celery_app
        
        # Check broker connection
        logger.info("Checking Celery broker connection...")
        
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            logger.info("✓ Celery broker is accessible")
            logger.info(f"Active workers: {list(active_workers.keys())}")
            
            # Check registered tasks
            registered_tasks = inspect.registered()
            if registered_tasks:
                for worker, tasks in registered_tasks.items():
                    logger.info(f"Worker {worker} has {len(tasks)} registered tasks")
                    crawler_tasks = [t for t in tasks if 'crawler' in t]
                    logger.info(f"  Crawler tasks: {len(crawler_tasks)}")
            
            return True
        else:
            logger.warning("No active Celery workers found")
            logger.info("Make sure to start a worker with: celery -A app.tasks worker --loglevel=info")
            return False
            
    except Exception as e:
        logger.error(f"Celery connection test failed: {e}")
        logger.info("Make sure Redis is running and Celery is configured correctly")
        return False

def main():
    """
    Main test function.
    """
    logger.info("Starting Celery Crawler Tests")
    
    # Test 1: Check Celery connection
    if not check_celery_connection():
        logger.error("Celery connection failed. Please start a worker first.")
        logger.info("Run: celery -A app.tasks worker --loglevel=info")
        return
    
    # Test 2: Run crawler tests
    if test_celery_crawler():
        logger.info("✓ All Celery crawler tests passed!")
    else:
        logger.error("✗ Some Celery tests failed")
        return
    
    # Test 3: Task monitoring
    test_task_monitoring()
    
    logger.info("\n" + "="*50)
    logger.info("ALL TESTS COMPLETED!")
    logger.info("="*50)

if __name__ == "__main__":
    main()