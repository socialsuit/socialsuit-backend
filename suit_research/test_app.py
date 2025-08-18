#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI application structure.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test core modules
        from app.core.config import settings
        print("✅ Config imported successfully")
        
        from app.core.database import Base, get_db
        print("✅ Database module imported successfully")
        
        # Test models
        from app.models.user import User
        from app.models.research import Research, ResearchCategory
        print("✅ Models imported successfully")
        
        # Test API modules
        from app.api.v1.api import api_router
        print("✅ API router imported successfully")
        
        # Test services
        from app.services.research_service import ResearchService
        print("✅ Services imported successfully")
        
        # Test main app
        from main import app
        print("✅ Main FastAPI app imported successfully")
        
        print("\n🎉 All imports successful! The application structure is correct.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_app_creation():
    """Test FastAPI app creation."""
    try:
        from main import app
        
        # Check if app is FastAPI instance
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            print("✅ FastAPI app created successfully")
            print(f"   App title: {app.title}")
            print(f"   App version: {app.version}")
            return True
        else:
            print("❌ App is not a FastAPI instance")
            return False
            
    except Exception as e:
        print(f"❌ Error creating app: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("SUIT RESEARCH - APPLICATION STRUCTURE TEST")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    print("\n" + "-" * 30)
    
    # Test app creation
    if not test_app_creation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! The application is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up environment: cp .env.template .env")
        print("3. Start databases (PostgreSQL, MongoDB, Redis)")
        print("4. Run migrations: alembic upgrade head")
        print("5. Start app: uvicorn main:app --reload")
    else:
        print("❌ SOME TESTS FAILED! Please check the errors above.")
    
    print("=" * 50)
    return success

if __name__ == "__main__":
    main()