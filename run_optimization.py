#!/usr/bin/env python3
"""
Database Optimization Runner Script

This script initializes and runs all database optimizations for the Social Suit application.
It sets up MongoDB indexes, PostgreSQL optimizations, Redis caching, and performance monitoring.

Usage:
    python run_optimization.py [--check-status] [--maintenance] [--full-init]

Options:
    --check-status    Check current optimization status
    --maintenance     Run maintenance tasks only
    --full-init       Run full initialization (default)
"""

import asyncio
import argparse
import sys
import logging
from datetime import datetime
from services.database.init_optimizations import (
    DatabaseOptimizationInitializer,
    initialize_database_optimizations,
    check_optimization_status,
    run_database_maintenance
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def run_status_check():
    """Check and display current optimization status."""
    print("🔍 Checking database optimization status...")
    print("=" * 60)
    
    try:
        status = await check_optimization_status()
        
        print(f"📊 Optimization Status Report")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # MongoDB Status
        mongodb_status = status.get('mongodb', {})
        print(f"🍃 MongoDB:")
        print(f"   Status: {'✅ Optimized' if mongodb_status.get('optimized') else '❌ Not Optimized'}")
        print(f"   Indexes: {mongodb_status.get('indexes_count', 0)}")
        print(f"   Collections: {len(mongodb_status.get('collections', []))}")
        
        # PostgreSQL Status
        postgresql_status = status.get('postgresql', {})
        print(f"🐘 PostgreSQL:")
        print(f"   Status: {'✅ Optimized' if postgresql_status.get('optimized') else '❌ Not Optimized'}")
        print(f"   Indexes: {postgresql_status.get('indexes_count', 0)}")
        print(f"   Materialized Views: {postgresql_status.get('materialized_views_count', 0)}")
        
        # Redis Status
        redis_status = status.get('redis', {})
        print(f"🔴 Redis:")
        print(f"   Status: {'✅ Optimized' if redis_status.get('optimized') else '❌ Not Optimized'}")
        print(f"   Memory Usage: {redis_status.get('memory_usage', 'Unknown')}")
        print(f"   Cache Patterns: {len(redis_status.get('cache_patterns', []))}")
        
        # Performance Monitoring
        monitoring_status = status.get('monitoring', {})
        print(f"📈 Performance Monitoring:")
        print(f"   Status: {'✅ Active' if monitoring_status.get('active') else '❌ Inactive'}")
        print(f"   Tracked Queries: {monitoring_status.get('tracked_queries', 0)}")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error checking optimization status: {e}")
        print(f"❌ Error checking status: {e}")
        return False
    
    return True

async def run_maintenance():
    """Run database maintenance tasks."""
    print("🔧 Running database maintenance...")
    print("=" * 60)
    
    try:
        results = await run_database_maintenance()
        
        print(f"📊 Maintenance Results")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # MongoDB Maintenance
        mongodb_results = results.get('mongodb', {})
        print(f"🍃 MongoDB Maintenance:")
        for task, result in mongodb_results.items():
            status = "✅ Success" if result.get('success') else "❌ Failed"
            print(f"   {task}: {status}")
            if result.get('details'):
                print(f"      Details: {result['details']}")
        
        # PostgreSQL Maintenance
        postgresql_results = results.get('postgresql', {})
        print(f"🐘 PostgreSQL Maintenance:")
        for task, result in postgresql_results.items():
            status = "✅ Success" if result.get('success') else "❌ Failed"
            print(f"   {task}: {status}")
            if result.get('details'):
                print(f"      Details: {result['details']}")
        
        # Redis Maintenance
        redis_results = results.get('redis', {})
        print(f"🔴 Redis Maintenance:")
        for task, result in redis_results.items():
            status = "✅ Success" if result.get('success') else "❌ Failed"
            print(f"   {task}: {status}")
            if result.get('details'):
                print(f"      Details: {result['details']}")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running maintenance: {e}")
        print(f"❌ Error running maintenance: {e}")
        return False
    
    return True

async def run_full_initialization():
    """Run full database optimization initialization."""
    print("🚀 Starting full database optimization initialization...")
    print("=" * 60)
    
    try:
        results = await initialize_database_optimizations()
        
        print(f"📊 Initialization Results")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # MongoDB Results
        mongodb_results = results.get('mongodb', {})
        print(f"🍃 MongoDB Optimization:")
        print(f"   Status: {'✅ Success' if mongodb_results.get('success') else '❌ Failed'}")
        print(f"   Indexes Created: {mongodb_results.get('indexes_created', 0)}")
        print(f"   Collections Optimized: {len(mongodb_results.get('collections_optimized', []))}")
        if mongodb_results.get('errors'):
            print(f"   Errors: {len(mongodb_results['errors'])}")
        
        # PostgreSQL Results
        postgresql_results = results.get('postgresql', {})
        print(f"🐘 PostgreSQL Optimization:")
        print(f"   Status: {'✅ Success' if postgresql_results.get('success') else '❌ Failed'}")
        print(f"   Indexes Created: {postgresql_results.get('indexes_created', 0)}")
        print(f"   Materialized Views: {postgresql_results.get('materialized_views_created', 0)}")
        if postgresql_results.get('errors'):
            print(f"   Errors: {len(postgresql_results['errors'])}")
        
        # Redis Results
        redis_results = results.get('redis', {})
        print(f"🔴 Redis Optimization:")
        print(f"   Status: {'✅ Success' if redis_results.get('success') else '❌ Failed'}")
        print(f"   Cache Patterns Set: {redis_results.get('cache_patterns_set', 0)}")
        print(f"   Memory Optimized: {'✅ Yes' if redis_results.get('memory_optimized') else '❌ No'}")
        if redis_results.get('errors'):
            print(f"   Errors: {len(redis_results['errors'])}")
        
        # Performance Monitoring Results
        monitoring_results = results.get('monitoring', {})
        print(f"📈 Performance Monitoring:")
        print(f"   Status: {'✅ Active' if monitoring_results.get('active') else '❌ Inactive'}")
        print(f"   Thresholds Set: {'✅ Yes' if monitoring_results.get('thresholds_configured') else '❌ No'}")
        
        print("=" * 60)
        
        # Overall Status
        overall_success = all([
            mongodb_results.get('success', False),
            postgresql_results.get('success', False),
            redis_results.get('success', False),
            monitoring_results.get('active', False)
        ])
        
        if overall_success:
            print("🎉 Database optimization completed successfully!")
            print("📚 See DATABASE_OPTIMIZATION_GUIDE.md for detailed documentation.")
        else:
            print("⚠️  Some optimizations failed. Check the logs for details.")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        print(f"❌ Error during initialization: {e}")
        return False
    
    return True

def main():
    """Main entry point for the optimization script."""
    parser = argparse.ArgumentParser(
        description="Database Optimization Runner for Social Suit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_optimization.py                    # Run full initialization
  python run_optimization.py --check-status    # Check current status
  python run_optimization.py --maintenance     # Run maintenance only
        """
    )
    
    parser.add_argument(
        '--check-status',
        action='store_true',
        help='Check current optimization status'
    )
    
    parser.add_argument(
        '--maintenance',
        action='store_true',
        help='Run maintenance tasks only'
    )
    
    parser.add_argument(
        '--full-init',
        action='store_true',
        help='Run full initialization (default)'
    )
    
    args = parser.parse_args()
    
    # Determine which operation to run
    if args.check_status:
        operation = run_status_check
        operation_name = "Status Check"
    elif args.maintenance:
        operation = run_maintenance
        operation_name = "Maintenance"
    else:
        operation = run_full_initialization
        operation_name = "Full Initialization"
    
    print(f"🔧 Social Suit Database Optimization")
    print(f"Operation: {operation_name}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Run the selected operation
        success = asyncio.run(operation())
        
        if success:
            print(f"✅ {operation_name} completed successfully!")
            sys.exit(0)
        else:
            print(f"❌ {operation_name} failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()