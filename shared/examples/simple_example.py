import os
import sys
import logging
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import the shared package
current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, os.path.dirname(parent_dir))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Example 1: Using JWT Authentication core functions
def jwt_auth_example():
    import hashlib
    from passlib.context import CryptContext
    from jose import jwt
    
    logger.info("Example 1: JWT Authentication Core Functions")
    
    # Create password context directly
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Hash a password
    password = "user_password"
    hashed_password = pwd_context.hash(password)
    logger.info(f"Original password: {password}")
    logger.info(f"Hashed password: {hashed_password}")
    
    # Verify password
    is_valid = pwd_context.verify(password, hashed_password)
    logger.info(f"Password verification result: {is_valid}")
    
    # Create a token manually
    secret_key = "example-secret-key"
    algorithm = "HS256"
    
    data = {"sub": "user@example.com", "user_id": 123}
    expire = datetime.utcnow() + timedelta(minutes=30)
    data.update({"exp": expire})
    
    encoded_jwt = jwt.encode(data, secret_key, algorithm=algorithm)
    logger.info(f"Generated JWT token: {encoded_jwt}")
    
    # Decode token
    try:
        payload = jwt.decode(encoded_jwt, secret_key, algorithms=[algorithm])
        logger.info(f"Decoded token payload: {payload}")
    except Exception as e:
        logger.error(f"Token decoding error: {str(e)}")

# Example 2: Using Common Utilities
def common_utils_example():
    import json
    import uuid
    import hashlib
    
    logger.info("\nExample 2: Common Utilities")
    
    # Generate hash
    data = "example data"
    hash_value = hashlib.md5(data.encode()).hexdigest()
    logger.info(f"Generated hash for '{data}': {hash_value}")
    
    # Generate UUID
    uuid_value = str(uuid.uuid4())
    logger.info(f"Generated UUID: {uuid_value}")
    
    # JSON serialization
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    complex_data = {
        "name": "Example User",
        "created_at": datetime.now(),
        "is_active": True,
        "scores": [95, 87, 92]
    }
    
    json_str = json.dumps(complex_data, cls=DateTimeEncoder)
    logger.info(f"Serialized JSON: {json_str}")

# Example 3: Using Redis Cache (simulation only)
def redis_cache_example():
    logger.info("\nExample 3: Redis Cache (Simulation)")
    
    # Simulate the behavior for demonstration
    def simulated_redis_cache(expire=300):
        def decorator(func):
            cache = {}
            def wrapper(*args, **kwargs):
                # Simulate cache key generation
                cache_key = f"{func.__name__}:{args}:{kwargs}"
                logger.info(f"Cache key: {cache_key}")
                
                # Simulate cache check
                if cache_key in cache:
                    logger.info(f"Cache hit for key: {cache_key}")
                    return cache[cache_key]
                
                logger.info(f"Cache miss. Executing function: {func.__name__}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Simulate storing in cache
                cache[cache_key] = result
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
    
    # Second call (cache hit)
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