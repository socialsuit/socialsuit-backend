# Integration Examples for Shared Library

This document provides examples of how to integrate the shared library components into both Social Suit and Sparkr projects.

## 1. Integrating JWT Authentication

### In Social Suit

```python
# social-suit/app/services/security/auth.py

from shared.auth.jwt import JWTAuth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Initialize JWT authentication with your configuration
jwt_auth = JWTAuth(
    secret_key="your-secret-key",  # Use environment variable in production
    access_token_expire_minutes=30
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt_auth.decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    # Get user from database
    user = get_user(username)  # Implement this function
    if user is None:
        raise credentials_exception
    return user
```

### In Sparkr

```python
# sparkr/app/core/security.py

from shared.auth.jwt import JWTAuth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db.session import get_session
from app.models.user import User

# Initialize JWT authentication with your configuration
jwt_auth = JWTAuth(
    secret_key="your-secret-key",  # Use environment variable in production
    access_token_expire_minutes=30
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt_auth.decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    # Get user from database
    user = await db.query(User).filter(User.email == username).first()
    if user is None:
        raise credentials_exception
    return user
```

## 2. Integrating Database Components

### In Social Suit

```python
# social-suit/app/services/database/database.py

from shared.database.sqlalchemy_base import get_db, get_db_session, init_db
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Initialize database
def setup_database():
    init_db(Base, "sqlite:///./social_suit.db")
```

### In Sparkr

```python
# sparkr/app/db/db/session.py

from shared.database.sqlalchemy_base import get_async_session, init_async_db
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Initialize database
async def setup_database():
    await init_async_db(Base, "postgresql+asyncpg://user:password@localhost/sparkr")
    
# Use in FastAPI dependency injection
get_session = get_async_session
```

## 3. Integrating Redis Cache

### In Social Suit

```python
# social-suit/app/services/database/redis.py

from shared.database.redis_manager import RedisManager, redis_cache

# Initialize Redis manager
redis_manager = RedisManager(
    host="localhost",
    port=6379,
    db=0,
    password=None
)

# Use the redis_cache decorator
@redis_cache(expire=300)
async def get_user_profile(user_id: int):
    # Expensive database operation
    return await db_get_user_profile(user_id)
```

### In Sparkr

```python
# sparkr/app/core/cache.py

from shared.database.redis_manager import RedisManager, redis_cache

# Initialize Redis manager
redis_manager = RedisManager(
    host="localhost",
    port=6379,
    db=0,
    password=None
)

# Use the redis_cache decorator
@redis_cache(expire=300)
async def get_user_posts(user_id: int):
    # Expensive database operation
    return await db_get_user_posts(user_id)
```

## 4. Integrating Security Middleware

### In Social Suit

```python
# social-suit/app/main.py

from fastapi import FastAPI
from shared.auth.security_middleware import SecurityMiddleware

app = FastAPI()

# Configure and apply security middleware
security_middleware = SecurityMiddleware(
    rate_limit_enabled=True,
    rate_limit_requests=100,
    rate_limit_window=60,  # 60 seconds
    security_headers_enabled=True,
    input_validation_enabled=True,
    ip_filtering_enabled=False,
    audit_logging_enabled=True
)

security_middleware.apply_to_app(app)
```

### In Sparkr

```python
# sparkr/app/main.py

from fastapi import FastAPI
from shared.auth.security_middleware import SecurityMiddleware

app = FastAPI()

# Configure and apply security middleware
security_middleware = SecurityMiddleware(
    rate_limit_enabled=True,
    rate_limit_requests=200,  # Different rate limit for Sparkr
    rate_limit_window=60,  # 60 seconds
    security_headers_enabled=True,
    input_validation_enabled=True,
    ip_filtering_enabled=True,  # Enable IP filtering for Sparkr
    allowed_ips=["192.168.1.0/24", "10.0.0.0/8"],  # Allow internal network
    audit_logging_enabled=True
)

security_middleware.apply_to_app(app)
```

## 5. Integrating Logging Utilities

### In Social Suit

```python
# social-suit/app/main.py

from shared.utils.logging_utils import setup_logging, RequestIdMiddleware
from fastapi import FastAPI
import logging

# Set up logging
setup_logging(
    log_level="INFO",
    log_format="json",
    log_file="logs/social_suit.log",
    rotate_logs=True,
    max_log_size_mb=10,
    backup_count=5
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Add request ID middleware
app.add_middleware(RequestIdMiddleware)

@app.on_event("startup")
async def startup_event():
    logger.info("Social Suit application starting up")
```

### In Sparkr

```python
# sparkr/app/main.py

from shared.utils.logging_utils import setup_logging, RequestIdMiddleware
from fastapi import FastAPI
import logging

# Set up logging
setup_logging(
    log_level="DEBUG",  # Different log level for Sparkr
    log_format="json",
    log_file="logs/sparkr.log",
    rotate_logs=True,
    max_log_size_mb=20,  # Different log size for Sparkr
    backup_count=10
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Add request ID middleware
app.add_middleware(RequestIdMiddleware)

@app.on_event("startup")
async def startup_event():
    logger.info("Sparkr application starting up")
```

## 6. Integrating Configuration Utilities

### In Social Suit

```python
# social-suit/app/config.py

from shared.utils.config import ConfigLoader

# Initialize config loader
config = ConfigLoader(
    config_file="config.yaml",
    env_prefix="SOCIAL_SUIT_",
    auto_reload=True
)

# Access configuration values
DATABASE_URL = config.get("database.url", "sqlite:///./social_suit.db")
REDIS_HOST = config.get("redis.host", "localhost")
REDIS_PORT = config.get("redis.port", 6379)
JWT_SECRET = config.get("security.jwt_secret", "your-secret-key")
```

### In Sparkr

```python
# sparkr/app/core/config.py

from shared.utils.config import ConfigLoader

# Initialize config loader
config = ConfigLoader(
    config_file="config.yaml",
    env_prefix="SPARKR_",
    auto_reload=True
)

# Access configuration values
DATABASE_URL = config.get("database.url", "postgresql+asyncpg://user:password@localhost/sparkr")
REDIS_HOST = config.get("redis.host", "localhost")
REDIS_PORT = config.get("redis.port", 6379)
JWT_SECRET = config.get("security.jwt_secret", "your-secret-key")
```

## 7. Using Common Utilities

### In Both Projects

```python
# Any file in either project

from shared.utils.common import (
    generate_hash,
    generate_uuid,
    json_serialize,
    json_deserialize,
    timing_decorator,
    async_timing_decorator,
    safe_execute,
    async_safe_execute,
    get_env_var
)

# Generate a unique ID
item_id = generate_uuid()

# Hash sensitive data
hashed_value = generate_hash("sensitive_data")

# Serialize complex objects to JSON
from datetime import datetime
data = {"timestamp": datetime.now(), "values": [1, 2, 3]}
json_data = json_serialize(data)

# Measure function execution time
@timing_decorator
def process_data(data):
    # Process data
    return result

# Safely execute a function with error handling
result = safe_execute(
    process_data,
    args=[data],
    default_value={},
    log_error=True
)

# Get environment variable with default value
api_key = get_env_var("API_KEY", "default-key")
```