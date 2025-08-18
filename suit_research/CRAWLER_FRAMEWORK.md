# Modular Crawler Framework

A comprehensive, modular web crawling framework built with Celery, designed to fetch, parse, normalize, and store content from various sources including HTML pages, RSS feeds, and JSON APIs.

## 🚀 Features

- **Modular Architecture**: Separate components for fetching, parsing, and normalizing data
- **Multi-Format Support**: HTML pages, RSS feeds, JSON APIs
- **Robots.txt Compliance**: Respects robots.txt directives
- **Rate Limiting**: Configurable request rate limiting
- **MongoDB Storage**: Stores raw and structured data in MongoDB
- **Celery Integration**: Asynchronous task processing with Celery
- **Scheduled Crawling**: Periodic crawling with Celery Beat
- **Error Handling**: Comprehensive error handling and logging
- **Health Monitoring**: Built-in health checks and statistics

## 📁 Project Structure

```
app/
├── crawlers/
│   ├── base_fetcher.py      # Generic fetcher with rate limiting and robots.txt
│   ├── base_parser.py       # Content parsing for HTML, RSS, JSON
│   ├── normalizer.py        # Data normalization and cleaning
│   └── base_crawler.py      # Legacy crawler (deprecated)
├── tasks/
│   └── crawler_tasks.py     # Celery tasks for crawling
├── core/
│   ├── celery_app.py        # Celery configuration
│   ├── mongodb.py           # MongoDB connection
│   └── config.py            # Application configuration
└── models/
    └── crawl.py             # MongoDB models

configs/
└── techcrunch_rss_config.py # Sample TechCrunch RSS configuration

demo_crawler.py              # Demo script
test_celery_crawler.py       # Celery testing script
```

## 🛠 Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables**:
   ```bash
   # .env file
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB_NAME=suit_research
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

3. **Start Required Services**:
   ```bash
   # Start MongoDB
   mongod
   
   # Start Redis
   redis-server
   ```

## 🚀 Quick Start

### 1. Start Celery Worker

```bash
# Start the Celery worker
celery -A app.tasks worker --loglevel=info

# Start Celery Beat (for scheduled tasks)
celery -A app.tasks beat --loglevel=info
```

### 2. Run Demo

```bash
# Test the framework directly
python demo_crawler.py

# Test Celery tasks
python test_celery_crawler.py
```

### 3. Submit Crawl Tasks

```python
from app.tasks.crawler_tasks import crawl_url_task

# Crawl a JSON API
result = crawl_url_task.delay(
    "https://httpbin.org/json",
    {"fetcher_type": "json", "timeout": 30}
)

# Crawl an RSS feed
from configs.techcrunch_rss_config import get_techcrunch_config
config = get_techcrunch_config("main")
result = crawl_url_task.delay(config["url"], config["config"])
```

## 📋 Components

### 1. Base Fetcher (`app/crawlers/base_fetcher.py`)

**Features**:
- Generic fetcher with auto-detection
- Specialized fetchers for HTML, RSS, JSON
- Rate limiting (configurable requests per second)
- Robots.txt compliance checking
- Request timeout handling
- Custom user agent support

**Usage**:
```python
from app.crawlers.base_fetcher import GenericFetcher

fetcher = GenericFetcher(
    requests_per_second=1.0,
    timeout=30,
    respect_robots=True
)
result = await fetcher.fetch("https://example.com")
```

### 2. Base Parser (`app/crawlers/base_parser.py`)

**Features**:
- Content-type specific parsing
- HTML metadata extraction
- RSS feed parsing
- JSON structure preservation
- Automatic parser selection

**Usage**:
```python
from app.crawlers.base_parser import GenericParser

parser = GenericParser()
parse_result = await parser.parse(fetch_result)
```

### 3. Normalizer (`app/crawlers/normalizer.py`)

**Features**:
- Data cleaning and standardization
- URL normalization
- Content categorization
- Entity extraction
- Database schema mapping

**Usage**:
```python
from app.crawlers.normalizer import GenericNormalizer

normalizer = GenericNormalizer()
normalized_data = await normalizer.normalize(parse_result)
```

### 4. Crawler Tasks (`app/tasks/crawler_tasks.py`)

**Available Tasks**:
- `crawl_url_task`: Main crawler task
- `crawl_rss_feed_task`: Specialized RSS crawler
- `crawl_api_endpoint_task`: Specialized JSON API crawler
- `cleanup_old_crawler_data`: Data cleanup
- `health_check_crawler`: Health monitoring

## ⚙️ Configuration

### Crawler Configuration

```python
config = {
    "fetcher_type": "auto",        # auto, html, rss, json
    "requests_per_second": 1.0,    # Rate limit
    "timeout": 30,                 # Request timeout
    "respect_robots": True,        # Respect robots.txt
    "user_agent": "Custom Bot/1.0" # Custom user agent
}
```

### TechCrunch RSS Example

```python
from configs.techcrunch_rss_config import get_techcrunch_config

# Get configuration for TechCrunch main feed
config = get_techcrunch_config("main")

# Available feeds: main, startups, funding, ai, apps, security, enterprise, gadgets
funding_config = get_techcrunch_config("funding")
```

## 📊 Data Storage

### Raw Crawls Collection

```javascript
{
  "_id": ObjectId("..."),
  "source": "https://example.com",
  "content": "...",
  "content_type": "text/html",
  "scraped_at": ISODate("..."),
  "metadata": {
    "status_code": 200,
    "headers": {...},
    "fetch_time": 1.23
  },
  "processing_status": "completed",
  "language": "en",
  "error_info": null,
  "retry_count": 0
}
```

### Structured Content Collection

```javascript
{
  "_id": ObjectId("..."),
  "raw_crawl_id": ObjectId("..."),
  "title": "Article Title",
  "description": "Article description...",
  "content": "Full article content...",
  "author": "Author Name",
  "published_date": ISODate("..."),
  "domain": "example.com",
  "category": "technology",
  "tags": ["tech", "ai"],
  "normalized_at": ISODate("...")
}
```

## 🔄 Scheduled Crawling

The framework includes pre-configured scheduled tasks:

```python
# Celery Beat Schedule
{
    "crawl-techcrunch-main": {
        "task": "app.tasks.crawler_tasks.crawl_rss_feed_task",
        "schedule": 7200.0,  # Every 2 hours
        "args": ["https://techcrunch.com/feed/", config]
    },
    "cleanup-old-crawler-data": {
        "task": "app.tasks.crawler_tasks.cleanup_old_crawler_data",
        "schedule": 86400.0,  # Daily
        "args": [30]  # Keep 30 days
    }
}
```

## 📈 Monitoring

### Health Checks

```python
from app.tasks.crawler_tasks import health_check_crawler

# Run health check
result = health_check_crawler.delay()
print(result.get())  # {"status": "healthy", ...}
```

### Statistics

The framework automatically tracks:
- Crawl success/failure rates
- Response times
- Content sizes
- Domain-specific metrics
- Daily aggregated statistics

## 🧪 Testing

### Run All Tests

```bash
# Test framework components
python demo_crawler.py

# Test Celery integration
python test_celery_crawler.py
```

### Manual Testing

```python
# Test specific fetcher
from app.crawlers.base_fetcher import RSSFetcher
import asyncio

async def test():
    fetcher = RSSFetcher()
    result = await fetcher.fetch("https://techcrunch.com/feed/")
    print(f"Status: {result.status_code}")
    print(f"Content length: {len(result.content)}")

asyncio.run(test())
```

## 🔧 Troubleshooting

### Common Issues

1. **Celery Worker Not Starting**:
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Check Celery configuration
   celery -A app.tasks inspect active
   ```

2. **MongoDB Connection Issues**:
   ```bash
   # Check MongoDB status
   mongosh --eval "db.adminCommand('ismaster')"
   ```

3. **Rate Limiting Issues**:
   - Adjust `requests_per_second` in configuration
   - Check robots.txt compliance
   - Verify user agent settings

4. **Memory Issues with Large Content**:
   - Implement content size limits in fetchers
   - Use streaming for large files
   - Increase worker memory limits

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test with verbose output
python demo_crawler.py
```

## 🚀 Production Deployment

### Scaling

1. **Multiple Workers**:
   ```bash
   # Start multiple workers
   celery -A app.tasks worker --concurrency=4 --loglevel=info
   ```

2. **Queue Separation**:
   ```bash
   # Dedicated crawler queue
   celery -A app.tasks worker --queues=crawler --loglevel=info
   ```

3. **Monitoring**:
   ```bash
   # Start Flower for monitoring
   celery -A app.tasks flower
   ```

### Performance Tuning

- Adjust `requests_per_second` based on target site limits
- Use connection pooling for database operations
- Implement caching for frequently accessed data
- Monitor memory usage and adjust worker settings

## 📝 API Reference

### Fetcher Classes

- `BaseFetcher`: Abstract base class
- `HTMLFetcher`: Specialized for HTML content
- `RSSFetcher`: Specialized for RSS feeds
- `JSONAPIFetcher`: Specialized for JSON APIs
- `GenericFetcher`: Auto-detecting fetcher

### Parser Classes

- `BaseParser`: Abstract base class
- `HTMLParser`: HTML content parsing
- `RSSParser`: RSS feed parsing
- `JSONParser`: JSON content parsing
- `GenericParser`: Auto-detecting parser

### Normalizer Classes

- `BaseNormalizer`: Abstract base class
- `HTMLNormalizer`: HTML content normalization
- `RSSNormalizer`: RSS content normalization
- `JSONNormalizer`: JSON content normalization
- `GenericNormalizer`: Auto-detecting normalizer

## 🤝 Contributing

1. Follow the modular architecture
2. Add comprehensive error handling
3. Include logging for debugging
4. Write tests for new components
5. Update documentation

## 📄 License

This project is part of the SuitResearch application and follows the same licensing terms.