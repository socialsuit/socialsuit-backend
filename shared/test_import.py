"""Test script to verify the shared-utils package installation."""

def test_imports():
    """Test importing key components from the shared package."""
    try:
        # Test importing from auth
        from shared.auth import create_access_token, hash_password
        print("✓ Auth imports successful")
        
        # Test importing from database
        from shared.database import create_db_engine, paginate_query
        print("✓ Database imports successful")
        
        # Test importing from logging
        from shared.logging import setup_logger, JsonFormatter
        print("✓ Logging imports successful")
        
        # Test importing from middleware
        from shared.middleware import RateLimiter, RequestLoggingMiddleware
        print("✓ Middleware imports successful")
        
        # Test importing from utils
        from shared.utils import format_datetime, validate_email
        print("✓ Utils imports successful")
        
        print("\nAll imports successful! The shared-utils package is installed correctly.")
        return True
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nThe shared-utils package may not be installed correctly.")
        print("Try installing it with: pip install -e shared/")
        return False


if __name__ == "__main__":
    test_imports()