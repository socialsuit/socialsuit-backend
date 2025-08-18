#!/usr/bin/env python3
"""
Database initialization script for Suit Research.
Sets up PostgreSQL tables via Alembic and MongoDB collections.
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.mongodb_setup import setup_mongodb
from app.core.config import settings


def run_alembic_upgrade():
    """Run Alembic upgrade to create PostgreSQL tables."""
    print("🔄 Running Alembic migrations...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], check=True, capture_output=True, text=True)
        
        print("✅ PostgreSQL tables created successfully")
        if result.stdout:
            print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Alembic migration failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


async def setup_databases():
    """Setup both PostgreSQL and MongoDB databases."""
    print("=" * 60)
    print("🗄️  DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Check if alembic.ini exists
    if not Path("alembic.ini").exists():
        print("❌ alembic.ini not found. Please run this script from the project root.")
        return False
    
    print(f"\n📋 Database Configuration:")
    print(f"   • PostgreSQL: {settings.DATABASE_URL}")
    print(f"   • MongoDB: {settings.MONGODB_URL}")
    print(f"   • Redis: {settings.REDIS_URL}")
    
    # Setup PostgreSQL with Alembic
    print(f"\n🐘 Setting up PostgreSQL...")
    if not run_alembic_upgrade():
        return False
    
    # Setup MongoDB
    print(f"\n🍃 Setting up MongoDB...")
    mongodb_success = await setup_mongodb()
    
    if not mongodb_success:
        print("❌ MongoDB setup failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n📊 Summary:")
    print("   ✅ PostgreSQL tables created")
    print("   ✅ MongoDB collections and indexes created")
    print("   ✅ Database schema is ready for use")
    
    print("\n🚀 Next Steps:")
    print("   1. Start the application: python start_dev.py")
    print("   2. Access API docs: http://localhost:8000/api/v1/docs")
    print("   3. Check health: http://localhost:8000/api/v1/status/health")
    
    return True


def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "DATABASE_URL",
        "MONGODB_URL", 
        "REDIS_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not hasattr(settings, var) or not getattr(settings, var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n💡 Please check your .env file and ensure all variables are set.")
        return False
    
    return True


async def main():
    """Main function."""
    print("🚀 SUIT RESEARCH - DATABASE INITIALIZATION")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup databases
    success = await setup_databases()
    
    if not success:
        print("\n❌ Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())