# Suit Research - FastAPI Backend

A production-ready FastAPI backend scaffold for research data management with web crawling capabilities.

## Features

- **FastAPI** with async support
- **PostgreSQL** for normalized data with SQLAlchemy ORM
- **MongoDB** for raw crawler dumps
- **Redis** for caching and rate limiting
- **Celery** for background tasks
- **Docker** containerization
- **Alembic** database migrations
- **Health checks** and monitoring

## Project Structure

```
suit_research/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── status.py      # Health checks
│   │       │   ├── research.py    # Research CRUD
│   │       │   └── crawler.py     # Crawler endpoints
│   │       └── api.py             # API router
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   ├── database.py            # PostgreSQL setup
│   │   ├── mongodb.py             # MongoDB setup
│   │   ├── redis_client.py        # Redis setup
│   │   └── celery_app.py          # Celery configuration
│   ├── models/
│   │   ├── user.py                # User model
│   │   └── research.py            # Research models
│   ├── services/
│   │   ├── research_service.py    # Research business logic
│   │   └── crawler_service.py     # Crawler business logic
│   ├── crawlers/
│   │   └── base_crawler.py        # Crawler implementations
│   ├── tasks/
│   │   ├── crawler_tasks.py       # Celery crawler tasks
│   │   ├── research_tasks.py      # Celery research tasks
│   │   └── notification_tasks.py  # Notification tasks
│   └── migrations/                # Alembic migrations
├── docker/
├── tests/
├── main.py                        # FastAPI application
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Multi-service setup
├── alembic.ini                    # Migration configuration
└── .env.template                  # Environment variables template
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd suit_research
   cp .env.template .env
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Verify health**:
   ```bash
   curl http://localhost:8000/api/v1/status/health
   ```

   Expected response:
   ```json
   {"status": "ok"}
   ```

### Local Development

1. **Setup environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup databases** (using Docker):
   ```bash
   docker-compose up postgres mongodb redis -d
   ```

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the application**:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Health Check
- `GET /api/v1/status/health` - Overall health check
- `GET /api/v1/status/ready` - Readiness probe
- `GET /api/v1/status/live` - Liveness probe

### Research
- `GET /api/v1/research/` - List research items
- `GET /api/v1/research/{id}` - Get research by ID
- `POST /api/v1/research/` - Create research item

### Crawler
- `POST /api/v1/crawler/start` - Start crawler task
- `GET /api/v1/crawler/status/{task_id}` - Get crawler status
- `GET /api/v1/crawler/data` - Get crawler results

## Configuration

Copy `.env.template` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/suit_research

# MongoDB
MONGODB_URL=mongodb://admin:admin123@localhost:27017/suit_research?authSource=admin

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Background Tasks

The application uses Celery for background processing:

- **Crawler tasks**: Web scraping and data extraction
- **Research tasks**: Data processing and analysis
- **Notification tasks**: Email and webhook notifications

Monitor tasks with Flower:
```bash
celery -A app.core.celery_app flower
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py
```

## Monitoring

### Health Checks
- Application: `http://localhost:8000/api/v1/status/health`
- Flower (Celery): `http://localhost:5555`

### Logs
```bash
# Application logs
docker-compose logs web

# Celery worker logs
docker-compose logs celery_worker

# All services
docker-compose logs
```

## Production Deployment

1. **Environment variables**: Set production values in `.env`
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **Monitoring**: Add Sentry, Prometheus, etc.
5. **Load balancer**: Use nginx or cloud load balancer
6. **SSL**: Configure HTTPS certificates

## Development

### Code Style
```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
```

### Adding New Features

1. **Models**: Add to `app/models/`
2. **Services**: Add business logic to `app/services/`
3. **Endpoints**: Add API routes to `app/api/v1/endpoints/`
4. **Tasks**: Add background tasks to `app/tasks/`
5. **Tests**: Add tests to `tests/`

## Troubleshooting

### Common Issues

1. **Database connection failed**:
   - Check if PostgreSQL is running
   - Verify DATABASE_URL in .env

2. **Redis connection failed**:
   - Check if Redis is running
   - Verify REDIS_URL in .env

3. **Celery tasks not running**:
   - Check if Celery worker is running
   - Verify CELERY_BROKER_URL in .env

4. **Health check fails**:
   - Check all service dependencies
   - Review application logs

### Reset Everything
```bash
# Stop all services
docker-compose down -v

# Remove all data
docker-compose down -v --remove-orphans

# Rebuild and start
docker-compose up --build
```

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request