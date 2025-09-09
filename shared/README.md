# Shared Utils for Social Suit and Sparkr

This shared library contains common components extracted from both Social Suit and Sparkr projects to promote code reuse, maintainability, and consistency across both applications.

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/socialsuit/shared-utils/releases/tag/v0.1.0)

## Structure

The shared library is organized into the following modules:

### Authentication (`shared/auth`)

- `jwt.py`: JWT authentication utilities including token generation, validation, and payload extraction
- `password.py`: Password hashing, verification, and validation utilities

### Database (`shared/database`)

- `connection.py`: Database connection management for SQLAlchemy
- `pagination.py`: Utilities for paginating database queries

### Logging (`shared/logging`)

- `logger.py`: Configurable logging with JSON formatting support

### Middleware (`shared/middleware`)

- `rate_limiter.py`: Configurable rate limiting middleware for FastAPI
- `request_logger.py`: Request logging middleware for FastAPI
- `exception_handlers.py`: Exception handlers for standardized error responses

### Utilities (`shared/utils`)

- `datetime.py`: Utilities for working with dates and times
- `validation.py`: Validation utilities for common data types
- `response_envelope.py`: Standard response envelope for API responses
- `response_wrapper.py`: Decorator and utilities for wrapping API responses

## Usage

### Installation

To use this shared library in your project, you can add it as a local dependency:

```bash
pip install -e shared/
```

Or include it in your `requirements.txt`:

```
-e ./shared/
```

### Versioning

This package follows [Semantic Versioning](https://semver.org/). When using this package in your applications, it's recommended to pin the version in your dependency specifications to ensure compatibility.

#### In requirements.txt

```
shared-utils==0.1.0
```

#### In pyproject.toml

```toml
dependencies = [
    "shared-utils==0.1.0",
]
```

#### Git Tags

Releases are also tagged in the repository using the format `v{major}.{minor}.{patch}` (e.g., `v0.1.0`). You can reference a specific version using git:

```
git+https://github.com/socialsuit/shared-utils.git@v0.1.0
```

See the [CHANGELOG.md](./CHANGELOG.md) for details about changes in each version.

### Examples

#### JWT Authentication

```python
from datetime import timedelta
from shared.auth import create_access_token, verify_password, hash_password

# Hash a password
hashed_password = hash_password("user_password")

# Verify a password
is_valid = verify_password("user_password", hashed_password)

# Create a token
token = create_access_token(
    subject="user_id",
    secret_key="your_secret_key",
    expires_delta=timedelta(minutes=30)
)

# Decode a token
from shared.auth.jwt import decode_token
payload = decode_token(token, "your_secret_key")
```

#### Response Envelope

The response envelope provides a standardized structure for all API responses:

```python
from fastapi import FastAPI, HTTPException
from shared.utils.response_envelope import ResponseEnvelope
from shared.utils.response_wrapper import envelope_response, create_error_response
from shared.middleware.exception_handlers import register_exception_handlers

# Create a FastAPI app
app = FastAPI()

# Register exception handlers
register_exception_handlers(app)

# Using the decorator to automatically wrap responses
@app.get("/items")
@envelope_response
async def get_items():
    return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

# Manually creating success responses
@app.get("/manual-success")
async def manual_success():
    return ResponseEnvelope.success_response(data={"message": "Success!"})

# Creating error responses
@app.get("/manual-error")
async def manual_error():
    return create_error_response(
        code="CUSTOM_ERROR",
        message="Something went wrong",
        status_code=400,
        details={"reason": "Invalid input"}
    )

# Raising exceptions that will be handled automatically
@app.get("/auto-error")
async def auto_error():
    raise HTTPException(status_code=404, detail="Resource not found")
```

The response structure will be:

```json
// Success response
{
  "success": true,
  "data": { ... },
  "error": null
}

// Error response
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

#### Database Operations

```python
from shared.database import create_db_engine, get_db_session, paginate_query
from sqlalchemy import select

# Create a database engine
engine = create_db_engine(
    driver="postgresql+asyncpg",
    username="user",
    password="password",
    host="localhost",
    port=5432,
    database="mydb"
)

# Use in a FastAPI dependency
async def get_db():
    async for session in get_db_session(engine):
        yield session

# Use pagination
async def get_users(session, page=1, size=10):
    query = select(User)
    return await paginate_query(session, query, page, size)
```

#### Logging

```python
from shared.logging import setup_logger

# Set up a logger
logger = setup_logger(
    name="my_app",
    level="INFO",
    json_format=True,
    log_file="app.log"
)

logger.info("Application started")
```

#### Middleware

```python
from fastapi import FastAPI
from shared.middleware import add_rate_limiter, add_request_logger

app = FastAPI()

# Add rate limiting
add_rate_limiter(
    app,
    redis_url="redis://localhost:6379/0",
    default_limit=100,
    default_window_seconds=60
)

# Add request logging
add_request_logger(app)
```

#### Utilities

```python
from datetime import datetime
from shared.utils import format_datetime, validate_email

# Format a datetime
formatted = format_datetime(datetime.now(), format_str="%Y-%m-%d")

# Validate an email
is_valid, error = validate_email("user@example.com")
```

## Running Tests

To run the tests, use pytest:

```bash
python -m pytest shared/tests/
```

Or to run tests for a specific module:

```bash
python -m pytest shared/tests/auth/
```

```python
from shared.utils.config import ConfigLoader, AppConfig

# Initialize configuration loader
config = ConfigLoader(
    config_path="config.yaml",
    env_prefix="APP",
    config_model=AppConfig
)

# Get configuration values
debug_mode = config.get("debug", False)
database_url = config.get("database.url")
```

#### Logging

```python
from shared.utils.logging_utils import setup_logging, get_logger

# Set up logging
setup_logging(log_format="json", log_file="app.log")

# Get a logger
logger = get_logger(__name__, {"service": "api"})
logger.info("Application started")
```

## Development

### Adding New Components

When adding new components to the shared library:

1. Ensure the component is truly common between both projects
2. Place it in the appropriate module based on its functionality
3. Create proper tests for the component
4. Update this README with usage examples

### Testing

To run tests for the shared library:

```bash
python -m pytest
```

## License

This shared library is for internal use only and is not licensed for external distribution.