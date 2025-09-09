import os
import sys
import logging

# Add the parent directory to sys.path to import the shared package
current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, os.path.dirname(parent_dir))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Example 1: Using JWT Authentication
def jwt_auth_example():
    from shared.auth.jwt import JWTAuth
    
    logger.info("Example 1: JWT Authentication")
    
    # Initialize JWT authentication
    jwt_auth = JWTAuth(
        secret_key="example-secret-key",
        access_token_expire_minutes=30
    )
    
    # Hash a password
    password = "user_password"
    hashed_password = jwt_auth.get_password_hash(password)
    logger.info(f"Original password: {password}")
    logger.info(f"Hashed password: {hashed_password}")
    
    # Verify password
    is_valid = jwt_auth.verify_password(password, hashed_password)
    logger.info(f"Password verification result: {is_valid}")
    
    # Create a token
    user_data = {"sub": "user@example.com", "user_id": 123}
    token = jwt_auth.create_access_token(user_data)
    logger.info(f"Generated JWT token: {token}")
    
    # Decode token
    try:
        payload = jwt_auth.decode_token(token)
        logger.info(f"Decoded token payload: {payload}")
    except Exception as e:
        logger.error(f"Token decoding error: {str(e)}")

# Example 2: Using Common Utilities
def common_utils_example():
    from shared.utils.common import generate_hash, generate_uuid, json_serialize
    
    logger.info("\nExample 2: Common Utilities")
    
    # Generate hash
    data = "example data"
    hash_value = generate_hash(data)
    logger.info(f"Generated hash for '{data}': {hash_value}")
    
    # Generate UUID
    uuid_value = generate_uuid()
    logger.info(f"Generated UUID: {uuid_value}")
    
    # JSON serialization
    from datetime import datetime
    complex_data = {
        "name": "Example User",
        "created_at": datetime.now(),
        "is_active": True,
        "scores": [95, 87, 92]
    }
    json_str = json_serialize(complex_data)
    logger.info(f"Serialized JSON: {json_str}")

# Example 3: Using Redis Cache (simulation only)
def redis_cache_example():
    logger.info("\nExample 3: Redis Cache (Simulation)")
    
    # In a real application, you would use:
    # from shared.database.redis_manager import RedisManager, redis_cache
    
    # Simulate the behavior for demonstration
    def simulated_redis_cache(expire=300):
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Simulate cache key generation
                cache_key = f"{func.__name__}:{args}:{kwargs}"
                logger.info(f"Cache key: {cache_key}")
                
                # Simulate cache check
                logger.info(f"Checking cache for key: {cache_key}")
                logger.info(f"Cache miss. Executing function: {func.__name__}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Simulate storing in cache
                logger.info(f"Storing result in cache with expiry: {expire} seconds")
                
                return result
            return wrapper
        return decorator
    
    # Example function with cache decorator
    @simulated_redis_cache(expire=60)
    def get_user_data(user_id):
        # Simulate expensive database operation
        logger.info(f"Performing expensive operation to get data for user {user_id}")
        return {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
    
    # First call (cache miss)
    user_data = get_user_data(123)
    logger.info(f"Retrieved user data: {user_data}")
    
    # Second call (would be cache hit in real implementation)
    logger.info("\nSecond call to the same function:")
    user_data = get_user_data(123)
    logger.info(f"Retrieved user data: {user_data}")

if __name__ == "__main__":
    logger.info("Starting shared library usage examples\n")
    
    # Run examples
    jwt_auth_example()
    common_utils_example()
    redis_cache_example()
    
    logger.info("\nAll examples completed successfully")