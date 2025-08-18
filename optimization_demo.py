#!/usr/bin/env python3
"""
Database Optimization Demo Script

This script demonstrates the usage of all optimization features implemented
in the Social Suit application, including performance tracking, caching,
and advanced database operations.

Usage:
    python optimization_demo.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from services.database.init_optimizations import initialize_database_optimizations
from services.repositories.user_repository import UserRepository
from services.scheduled_post_service import ScheduledPostService
from services.analytics.data_analyzer import AnalyticsAnalyzer
from services.analytics.data_collector import AnalyticsCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_user_operations():
    """Demonstrate optimized user operations."""
    print("\n🔍 Demonstrating User Repository Optimizations")
    print("-" * 50)
    
    user_repo = UserRepository()
    
    # Get user with caching
    print("1. Getting user by email (with caching)...")
    user = await user_repo.get_by_email("demo@example.com")
    if user:
        print(f"   ✅ Found user: {user.get('username', 'Unknown')}")
    else:
        print("   ℹ️  User not found")
    
    # Get user statistics with aggregation
    print("2. Getting user statistics (30 days)...")
    stats = await user_repo.get_user_statistics(days=30)
    print(f"   📊 Total posts: {stats.get('total_posts', 0)}")
    print(f"   📈 Avg engagement: {stats.get('avg_engagement_rate', 0):.2f}%")
    
    # Search users with pagination
    print("3. Searching users with pagination...")
    users = await user_repo.search_users("demo", limit=5, offset=0)
    print(f"   🔍 Found {len(users)} users")
    
    # Get user metrics trends
    print("4. Getting user metrics trends...")
    trends = await user_repo.get_user_metrics_trends(days=7)
    print(f"   📈 Trend data points: {len(trends)}")

async def demo_scheduled_post_operations():
    """Demonstrate optimized scheduled post operations."""
    print("\n📅 Demonstrating Scheduled Post Service Optimizations")
    print("-" * 50)
    
    post_service = ScheduledPostService()
    
    # Get user scheduled posts with caching and pagination
    print("1. Getting user scheduled posts (with caching)...")
    posts = await post_service.get_user_scheduled_posts(
        user_id="demo_user_123",
        platform="twitter",
        limit=10,
        offset=0
    )
    print(f"   📝 Found {len(posts)} scheduled posts")
    
    # Get post statistics
    print("2. Getting post statistics...")
    stats = await post_service.get_post_statistics(
        user_id="demo_user_123",
        days=30
    )
    print(f"   📊 Total posts: {stats.get('total_posts', 0)}")
    print(f"   ✅ Published: {stats.get('published_posts', 0)}")
    print(f"   ⏳ Pending: {stats.get('pending_posts', 0)}")
    print(f"   ❌ Failed: {stats.get('failed_posts', 0)}")
    
    # Get platform performance
    print("3. Getting platform performance metrics...")
    performance = await post_service.get_platform_performance(
        user_id="demo_user_123",
        days=30
    )
    for platform, metrics in performance.items():
        print(f"   📱 {platform.title()}: {metrics.get('success_rate', 0):.1f}% success rate")
    
    # Search posts
    print("4. Searching posts by content...")
    search_results = await post_service.search_posts(
        user_id="demo_user_123",
        query="social media",
        limit=5
    )
    print(f"   🔍 Found {len(search_results)} matching posts")

async def demo_analytics_operations():
    """Demonstrate optimized analytics operations."""
    print("\n📈 Demonstrating Analytics Service Optimizations")
    print("-" * 50)
    
    analyzer = AnalyticsAnalyzer()
    collector = AnalyticsCollector()
    
    # Get user overview with caching
    print("1. Getting user analytics overview (with caching)...")
    overview = await analyzer.get_user_overview(
        user_id="demo_user_123",
        days=30
    )
    print(f"   👥 Total followers: {overview.get('total_followers', 0):,}")
    print(f"   💬 Total engagement: {overview.get('total_engagement', 0):,}")
    print(f"   📊 Engagement rate: {overview.get('engagement_rate', 0):.2f}%")
    
    # Get platform insights
    print("2. Getting platform insights...")
    insights = await analyzer.get_platform_insights(
        user_id="demo_user_123",
        platform="twitter",
        days=30
    )
    print(f"   🐦 Twitter followers: {insights.get('followers', 0):,}")
    print(f"   📈 Growth rate: {insights.get('growth_rate', 0):.2f}%")
    
    # Get content recommendations
    print("3. Getting AI-powered content recommendations...")
    recommendations = await analyzer.get_content_recommendations(
        user_id="demo_user_123",
        platform="twitter"
    )
    print(f"   🎯 Generated {len(recommendations.get('recommendations', []))} recommendations")
    
    # Collect analytics data
    print("4. Collecting analytics data...")
    collection_result = await collector.collect_user_analytics(
        user_id="demo_user_123",
        platforms=["twitter", "facebook", "instagram"]
    )
    print(f"   📊 Collected data for {len(collection_result.get('platforms', []))} platforms")

async def demo_caching_performance():
    """Demonstrate caching performance improvements."""
    print("\n⚡ Demonstrating Caching Performance")
    print("-" * 50)
    
    analyzer = AnalyticsAnalyzer()
    
    # First call (cache miss)
    print("1. First call (cache miss)...")
    start_time = datetime.now()
    overview1 = await analyzer.get_user_overview("demo_user_123", days=30)
    first_call_time = (datetime.now() - start_time).total_seconds()
    print(f"   ⏱️  First call time: {first_call_time:.3f} seconds")
    
    # Second call (cache hit)
    print("2. Second call (cache hit)...")
    start_time = datetime.now()
    overview2 = await analyzer.get_user_overview("demo_user_123", days=30)
    second_call_time = (datetime.now() - start_time).total_seconds()
    print(f"   ⚡ Second call time: {second_call_time:.3f} seconds")
    
    # Performance improvement
    if first_call_time > 0:
        improvement = ((first_call_time - second_call_time) / first_call_time) * 100
        print(f"   🚀 Performance improvement: {improvement:.1f}%")

async def demo_bulk_operations():
    """Demonstrate bulk operations for efficiency."""
    print("\n📦 Demonstrating Bulk Operations")
    print("-" * 50)
    
    post_service = ScheduledPostService()
    
    # Simulate bulk status update
    print("1. Bulk status update...")
    post_ids = [1, 2, 3, 4, 5]  # Example post IDs
    success = await post_service.bulk_update_status(
        post_ids=post_ids,
        status="published"
    )
    print(f"   📝 Bulk update {'✅ successful' if success else '❌ failed'}")
    
    # Get posts by time range
    print("2. Getting posts by time range...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    posts = await post_service.get_posts_by_timerange(
        user_id="demo_user_123",
        start_date=start_date,
        end_date=end_date
    )
    print(f"   📅 Found {len(posts)} posts in the last 7 days")

async def run_optimization_demo():
    """Run the complete optimization demonstration."""
    print("🚀 Social Suit Database Optimization Demo")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize optimizations first
        print("\n🔧 Initializing database optimizations...")
        init_results = await initialize_database_optimizations()
        
        if init_results.get('mongodb', {}).get('success') and \
           init_results.get('postgresql', {}).get('success') and \
           init_results.get('redis', {}).get('success'):
            print("✅ Database optimizations initialized successfully!")
        else:
            print("⚠️  Some optimizations may not be fully initialized")
        
        # Run demonstrations
        await demo_user_operations()
        await demo_scheduled_post_operations()
        await demo_analytics_operations()
        await demo_caching_performance()
        await demo_bulk_operations()
        
        print("\n" + "=" * 60)
        print("🎉 Optimization demo completed successfully!")
        print("\n📚 Key Features Demonstrated:")
        print("   • Performance tracking with decorators")
        print("   • Multi-level caching with Redis")
        print("   • Optimized database queries")
        print("   • Bulk operations for efficiency")
        print("   • Advanced analytics and insights")
        print("   • Automated cache invalidation")
        print("   • Pagination for large datasets")
        print("   • AI-powered recommendations")
        
        print("\n📖 For detailed documentation, see:")
        print("   • DATABASE_OPTIMIZATION_GUIDE.md")
        print("   • Individual service README files")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure all databases are running")
        print("   2. Check environment variables")
        print("   3. Verify network connectivity")
        print("   4. Run: python run_optimization.py --check-status")

def main():
    """Main entry point for the demo."""
    try:
        asyncio.run(run_optimization_demo())
    except KeyboardInterrupt:
        print("\n⚠️  Demo cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()