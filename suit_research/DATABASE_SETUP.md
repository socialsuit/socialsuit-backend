# Database Setup and Migration Guide

## Overview
This guide covers the complete database schema setup for the Suit Research project, including PostgreSQL tables and MongoDB collections.

## Database Schema

### PostgreSQL Tables
- **users** - User accounts and authentication
- **projects** - Cryptocurrency/blockchain projects
- **investors** - Investment firms and individuals
- **funding_rounds** - Investment rounds data
- **investors_portfolio** - Junction table for investor-project relationships
- **api_keys** - API authentication keys
- **webhooks** - Webhook configurations
- **alerts** - User alert configurations
- **watchlists** - User project watchlists
- **research_categories** - Research categorization
- **research** - Research content

### MongoDB Collections
- **raw_crawls** - Raw HTML crawl data with metadata
- **crawl_stats** - Crawling statistics and performance metrics

## Quick Start with Docker

### 1. Start Database Services
```bash
# Start PostgreSQL and MongoDB
docker-compose up -d postgres mongodb redis
```

### 2. Initialize Databases
```bash
# Run database initialization
python init_database.py
```

### 3. Validate Schema
```bash
# Test the schema
python test_database_schema.py
```

## Manual Setup

### PostgreSQL Setup
1. **Create Database**:
   ```sql
   CREATE DATABASE suit_research;
   ```

2. **Run Migrations**:
   ```bash
   # Generate migration (if needed)
   alembic revision --autogenerate -m "Initial schema"
   
   # Apply migrations
   alembic upgrade head
   ```

### MongoDB Setup
1. **Create Collections and Indexes**:
   ```bash
   python -c "from app.core.mongodb_setup import setup_mongodb; setup_mongodb()"
   ```

## Environment Variables

Ensure these are set in your `.env` file:

```env
# PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/suit_research

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=suit_research

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Schema Validation

The `test_database_schema.py` script validates:
- ✅ SQLAlchemy model definitions
- ✅ Model relationships
- ✅ Field presence and types
- ✅ MongoDB model schemas
- 🐘 PostgreSQL table creation (requires running DB)

## Key Features

### Indexes Created
- `projects.slug` - Fast project lookups
- `funding_rounds.announced_at` - Time-based queries
- `investors.name` - Investor search
- `raw_crawls.source` - Source-based filtering
- `raw_crawls.scraped_at` - Time-based crawl queries

### Relationships
- Projects ↔ Funding Rounds (1:many)
- Projects ↔ Investors (many:many via portfolio)
- Users ↔ Alerts/Watchlists (1:many)
- All models include proper foreign key constraints

### Data Types
- JSON fields for flexible metadata storage
- Proper timestamp handling with timezone support
- Decimal precision for financial amounts
- Text fields with appropriate length limits

## Troubleshooting

### Common Issues

1. **SQLAlchemy Reserved Names**:
   - Fixed: `metadata` → `meta_data`
   - Avoids conflicts with SQLAlchemy internals

2. **Pydantic v2 Compatibility**:
   - Updated `PyObjectId` for Pydantic v2
   - Uses `__get_pydantic_core_schema__` instead of `__get_validators__`

3. **Migration Conflicts**:
   ```bash
   # Reset migrations if needed
   alembic downgrade base
   alembic upgrade head
   ```

## Next Steps

1. **Start Services**: `docker-compose up -d`
2. **Initialize DB**: `python init_database.py`
3. **Validate**: `python test_database_schema.py`
4. **Develop**: Start adding your application logic!

## Files Created

### Models
- `app/models/project.py` - Project model
- `app/models/funding.py` - Funding round model
- `app/models/investor.py` - Investor and portfolio models
- `app/models/api.py` - API key and webhook models
- `app/models/alert.py` - Alert and watchlist models
- `app/models/crawl.py` - MongoDB crawl models
- `app/models/user.py` - Updated user model

### Migrations
- `app/migrations/versions/001_initial_schema.py` - Complete schema migration

### Setup Scripts
- `init_database.py` - Database initialization
- `app/core/mongodb_setup.py` - MongoDB setup utilities
- `test_database_schema.py` - Schema validation

The database schema is now ready for production use! 🚀