#!/usr/bin/env python3
"""
Startup script for the modular crawler framework.

This script helps users quickly start the crawler system and run basic tests.
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required services are running."""
    logger.info("Checking dependencies...")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        logger.info("✓ Redis is running")
    except Exception as e:
        logger.error(f"✗ Redis is not accessible: {e}")
        logger.info("Please start Redis: redis-server")
        return False
    
    # Check MongoDB
    try:
        import pymongo
        client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        logger.info("✓ MongoDB is running")
    except Exception as e:
        logger.error(f"✗ MongoDB is not accessible: {e}")
        logger.info("Please start MongoDB: mongod")
        return False
    
    return True

def install_dependencies():
    """Install required Python packages."""
    logger.info("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to install dependencies: {e}")
        return False

def start_celery_worker():
    """Start Celery worker in background."""
    logger.info("Starting Celery worker...")
    
    try:
        # Start worker in background
        worker_cmd = [
            sys.executable, "-m", "celery", 
            "-A", "app.tasks", "worker", 
            "--loglevel=info",
            "--concurrency=2"
        ]
        
        worker_process = subprocess.Popen(
            worker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if it's still running
        if worker_process.poll() is None:
            logger.info("✓ Celery worker started successfully")
            return worker_process
        else:
            stdout, stderr = worker_process.communicate()
            logger.error(f"✗ Celery worker failed to start")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"✗ Failed to start Celery worker: {e}")
        return None

def start_celery_beat():
    """Start Celery beat scheduler in background."""
    logger.info("Starting Celery beat scheduler...")
    
    try:
        beat_cmd = [
            sys.executable, "-m", "celery",
            "-A", "app.tasks", "beat",
            "--loglevel=info"
        ]
        
        beat_process = subprocess.Popen(
            beat_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        if beat_process.poll() is None:
            logger.info("✓ Celery beat scheduler started successfully")
            return beat_process
        else:
            stdout, stderr = beat_process.communicate()
            logger.error(f"✗ Celery beat failed to start")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"✗ Failed to start Celery beat: {e}")
        return None

def run_demo():
    """Run the demo crawler."""
    logger.info("Running crawler demo...")
    
    try:
        # Run demo script
        result = subprocess.run(
            [sys.executable, "demo_crawler.py"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout
        )
        
        if result.returncode == 0:
            logger.info("✓ Demo completed successfully")
            logger.info("Demo output:")
            print(result.stdout)
            return True
        else:
            logger.error("✗ Demo failed")
            logger.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ Demo timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to run demo: {e}")
        return False

def test_celery_tasks():
    """Test Celery tasks."""
    logger.info("Testing Celery tasks...")
    
    try:
        # Run Celery test script
        result = subprocess.run(
            [sys.executable, "test_celery_crawler.py"],
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes timeout
        )
        
        if result.returncode == 0:
            logger.info("✓ Celery tests completed successfully")
            return True
        else:
            logger.error("✗ Celery tests failed")
            logger.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ Celery tests timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to run Celery tests: {e}")
        return False

def submit_sample_task():
    """Submit a sample crawl task."""
    logger.info("Submitting sample crawl task...")
    
    try:
        from app.tasks.crawler_tasks import crawl_url_task
        
        # Submit a simple task
        test_url = "https://httpbin.org/json"
        config = {
            "fetcher_type": "json",
            "requests_per_second": 2.0,
            "timeout": 15
        }
        
        task = crawl_url_task.delay(test_url, config)
        logger.info(f"Task submitted with ID: {task.id}")
        
        # Wait for result
        result = task.get(timeout=60)
        logger.info("✓ Sample task completed successfully")
        logger.info(f"Result: {result.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to submit sample task: {e}")
        return False

def show_usage():
    """Show usage instructions."""
    print(f"""
{'='*60}
MODULAR CRAWLER FRAMEWORK - QUICK START
{'='*60}

The crawler framework is now ready! Here's what you can do:

1. MANUAL TASK SUBMISSION:
   python -c "
   from app.tasks.crawler_tasks import crawl_url_task
   result = crawl_url_task.delay('https://httpbin.org/json', {{'fetcher_type': 'json'}})
   print('Task ID:', result.id)
   print('Result:', result.get())
   "

2. TECHCRUNCH RSS CRAWLING:
   python -c "
   from configs.techcrunch_rss_config import get_techcrunch_config
   from app.tasks.crawler_tasks import crawl_rss_feed_task
   config = get_techcrunch_config('main')
   result = crawl_rss_feed_task.delay(config['url'], config['config'])
   print('RSS Task ID:', result.id)
   "

3. MONITOR TASKS:
   # Start Flower (web UI)
   celery -A app.tasks flower
   # Then visit: http://localhost:5555

4. CHECK MONGODB DATA:
   mongosh suit_research --eval "db.raw_crawls.find().limit(5).pretty()"

5. VIEW LOGS:
   # Worker logs are in the terminal where you started the worker
   # Beat logs are in the terminal where you started beat

6. STOP SERVICES:
   # Press Ctrl+C in the terminals running worker and beat

{'='*60}
SCHEDULED CRAWLING:
{'='*60}

The following tasks are scheduled automatically:
- TechCrunch main feed: Every 2 hours
- TechCrunch funding feed: Every 4 hours  
- TechCrunch AI feed: Every 6 hours
- Crawler health check: Every 5 minutes
- Data cleanup: Daily (keeps 30 days)

{'='*60}
""")

def main():
    """Main startup function."""
    logger.info("Starting Modular Crawler Framework")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        logger.error("Please start required services and try again")
        sys.exit(1)
    
    # Step 2: Install dependencies (if needed)
    if not os.path.exists("requirements.txt"):
        logger.error("requirements.txt not found. Please run from project root.")
        sys.exit(1)
    
    # Step 3: Start Celery worker
    worker_process = start_celery_worker()
    if not worker_process:
        logger.error("Failed to start Celery worker")
        sys.exit(1)
    
    # Step 4: Start Celery beat (optional)
    beat_process = start_celery_beat()
    
    try:
        # Step 5: Run tests
        logger.info("\n" + "="*50)
        logger.info("RUNNING TESTS")
        logger.info("="*50)
        
        # Test framework directly
        if run_demo():
            logger.info("✓ Framework demo passed")
        else:
            logger.warning("⚠ Framework demo had issues")
        
        # Test Celery integration
        if test_celery_tasks():
            logger.info("✓ Celery integration tests passed")
        else:
            logger.warning("⚠ Celery tests had issues")
        
        # Submit sample task
        if submit_sample_task():
            logger.info("✓ Sample task submission passed")
        else:
            logger.warning("⚠ Sample task had issues")
        
        # Step 6: Show usage
        show_usage()
        
        # Keep running
        logger.info("Crawler framework is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(10)
                # Check if processes are still running
                if worker_process.poll() is not None:
                    logger.error("Celery worker stopped unexpectedly")
                    break
                if beat_process and beat_process.poll() is not None:
                    logger.warning("Celery beat stopped unexpectedly")
        
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    
    finally:
        # Cleanup
        if worker_process and worker_process.poll() is None:
            logger.info("Stopping Celery worker...")
            worker_process.terminate()
            worker_process.wait()
        
        if beat_process and beat_process.poll() is None:
            logger.info("Stopping Celery beat...")
            beat_process.terminate()
            beat_process.wait()
        
        logger.info("Crawler framework stopped")

if __name__ == "__main__":
    main()