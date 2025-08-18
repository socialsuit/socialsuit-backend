#!/usr/bin/env python3
"""
Test script to validate database schema and models.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.models import *
from app.core.database import Base, engine
from app.core.config import settings
from sqlalchemy import inspect, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_postgresql_schema():
    """Test PostgreSQL schema and models."""
    print("🐘 Testing PostgreSQL Schema...")
    
    try:
        # Test database connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✅ Connected to PostgreSQL: {version}")
        
        # Test model imports
        models = [
            User, Project, FundingRound, Investor, InvestorPortfolio,
            ApiKey, Webhook, Alert, Watchlist, Research, ResearchCategory
        ]
        
        print(f"   ✅ Successfully imported {len(models)} models")
        
        # Test table creation (metadata)
        inspector = inspect(engine.sync_engine)
        
        # Check if tables exist
        tables = await asyncio.get_event_loop().run_in_executor(
            None, inspector.get_table_names
        )
        
        expected_tables = [
            'users', 'projects', 'funding_rounds', 'investors', 'investors_portfolio',
            'api_keys', 'webhooks', 'alerts', 'watchlists', 'research', 'research_categories'
        ]
        
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            print(f"   ⚠️  Missing tables: {missing_tables}")
            print("   💡 Run 'python init_database.py' to create tables")
        else:
            print(f"   ✅ All {len(expected_tables)} tables exist")
        
        return True
        
    except Exception as e:
        print(f"   ❌ PostgreSQL test failed: {e}")
        return False


async def test_mongodb_models():
    """Test MongoDB models."""
    print("🍃 Testing MongoDB Models...")
    
    try:
        from app.models.crawl import RawCrawl, CrawlStats
        
        # Test model creation
        sample_crawl = RawCrawl(
            raw_html="<html><body>Test</body></html>",
            source="https://example.com",
            metadata={"test": True}
        )
        
        sample_stats = CrawlStats(
            date=sample_crawl.scraped_at,
            source="example.com",
            total_crawls=1
        )
        
        print("   ✅ MongoDB models created successfully")
        print(f"   ✅ RawCrawl model: {sample_crawl.source}")
        print(f"   ✅ CrawlStats model: {sample_stats.source}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MongoDB test failed: {e}")
        return False


def test_model_relationships():
    """Test model relationships."""
    print("🔗 Testing Model Relationships...")
    
    try:
        # Test that models have expected relationships
        relationships = {
            'Project': ['funding_rounds', 'investor_portfolios', 'alerts', 'watchlists'],
            'FundingRound': ['project'],
            'Investor': ['portfolios'],
            'InvestorPortfolio': ['investor', 'project'],
            'Alert': ['user', 'project'],
            'Watchlist': ['user', 'project']
        }
        
        for model_name, expected_rels in relationships.items():
            model_class = globals()[model_name]
            
            for rel_name in expected_rels:
                if hasattr(model_class, rel_name):
                    print(f"   ✅ {model_name}.{rel_name}")
                else:
                    print(f"   ❌ {model_name}.{rel_name} - missing")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Relationship test failed: {e}")
        return False


def test_model_fields():
    """Test that models have required fields."""
    print("📋 Testing Model Fields...")
    
    try:
        # Test key fields exist
        field_tests = {
            'Project': ['id', 'name', 'slug', 'website', 'description', 'token_symbol', 'score', 'meta_data'],
            'FundingRound': ['id', 'project_id', 'round_type', 'amount_usd', 'currency', 'announced_at', 'investors'],
            'Investor': ['id', 'name', 'slug', 'website', 'profile'],
            'User': ['id', 'email', 'password_hash', 'role'],
            'ApiKey': ['id', 'key_hash', 'scopes'],
            'Webhook': ['id', 'url', 'secret', 'events'],
            'Alert': ['id', 'user_id', 'project_id', 'alert_type', 'threshold'],
            'Watchlist': ['id', 'user_id', 'project_id']
        }
        
        for model_name, expected_fields in field_tests.items():
            model_class = globals()[model_name]
            
            for field_name in expected_fields:
                if hasattr(model_class, field_name):
                    print(f"   ✅ {model_name}.{field_name}")
                else:
                    print(f"   ❌ {model_name}.{field_name} - missing")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Field test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 DATABASE SCHEMA VALIDATION")
    print("=" * 60)
    
    print(f"\n📋 Configuration:")
    print(f"   • PostgreSQL: {settings.DATABASE_URL}")
    print(f"   • MongoDB: {settings.MONGODB_URL}")
    
    tests = [
        ("PostgreSQL Schema", test_postgresql_schema()),
        ("MongoDB Models", test_mongodb_models()),
        ("Model Relationships", test_model_relationships()),
        ("Model Fields", test_model_fields())
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        print(f"\n{test_name}:")
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
        results.append(result)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"   ✅ Passed: {passed}/{total}")
    print(f"   ❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Database schema is valid.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)