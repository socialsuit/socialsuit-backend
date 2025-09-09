import os
import json
import logging
import hashlib
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
from functools import wraps
import time

logger = logging.getLogger(__name__)

# JSON serialization helpers
class JSONEncoder(json.JSONEncoder):
    """Enhanced JSON encoder that handles additional types."""
    
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)

def json_serialize(obj: Any) -> str:
    """Serialize an object to JSON string with enhanced type handling."""
    return json.dumps(obj, cls=JSONEncoder)

def json_deserialize(json_str: str) -> Any:
    """Deserialize a JSON string to Python object."""
    return json.loads(json_str)

# Hashing utilities
def generate_hash(data: Any, algorithm: str = "sha256") -> str:
    """Generate a hash from any data.
    
    Args:
        data: Data to hash (will be converted to string)
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        Hexadecimal string representation of the hash
    """
    if not isinstance(data, str):
        data = str(data)
    
    data = data.encode("utf-8")
    
    if algorithm == "md5":
        return hashlib.md5(data).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(data).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(data).hexdigest()
    else:  # Default to sha256
        return hashlib.sha256(data).hexdigest()

def generate_uuid() -> str:
    """Generate a random UUID."""
    return str(uuid.uuid4())

# Performance monitoring
def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure and log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Log execution time if it's slow (over 100ms)
        if execution_time > 0.1:
            logger.warning(f"Slow operation: {func.__name__} took {execution_time:.4f} seconds")
        else:
            logger.debug(f"Operation: {func.__name__} took {execution_time:.4f} seconds")
            
        return result
    return wrapper

# Async version of timing decorator
def async_timing_decorator(func: Callable) -> Callable:
    """Decorator to measure and log async function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Log execution time if it's slow (over 100ms)
        if execution_time > 0.1:
            logger.warning(f"Slow async operation: {func.__name__} took {execution_time:.4f} seconds")
        else:
            logger.debug(f"Async operation: {func.__name__} took {execution_time:.4f} seconds")
            
        return result
    return wrapper

# Environment helpers
def get_env_variable(name: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable with type conversion.
    
    Args:
        name: Name of the environment variable
        default: Default value if not found
        required: If True, raises ValueError when variable is not found
        
    Returns:
        Value of the environment variable, converted to appropriate type
    """
    value = os.environ.get(name)
    
    if value is None:
        if required:
            raise ValueError(f"Required environment variable {name} is not set")
        return default
    
    # Try to convert to appropriate type based on default
    if default is not None:
        if isinstance(default, bool):
            return value.lower() in ("true", "yes", "1", "t")
        elif isinstance(default, int):
            return int(value)
        elif isinstance(default, float):
            return float(value)
        elif isinstance(default, list):
            return value.split(",")
    
    return value

# Error handling
def safe_execute(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """Execute a function safely, returning default value on exception.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        default_return: Value to return if an exception occurs
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function result or default_return on exception
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {str(e)}")
        return default_return

# Async version of safe_execute
async def safe_execute_async(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """Execute an async function safely, returning default value on exception.
    
    Args:
        func: Async function to execute
        *args: Arguments to pass to the function
        default_return: Value to return if an exception occurs
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function result or default_return on exception
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing async {func.__name__}: {str(e)}")
        return default_return