# Installing and Using the Shared Library

This document provides instructions for installing and using the shared library in both Social Suit and Sparkr projects.

## Installation

There are two ways to install the shared library:

### 1. Development Mode (Recommended during development)

This method creates a symlink to the shared library, allowing you to make changes to the shared code and have them immediately reflected in both projects without reinstalling.

```bash
# Navigate to the shared library directory
cd /path/to/social_suit/shared

# Install in development mode
pip install -e .
```

### 2. Regular Installation

This method installs a copy of the shared library. If you make changes to the shared code, you'll need to reinstall it.

```bash
# Navigate to the shared library directory
cd /path/to/social_suit/shared

# Install the package
pip install .
```

## Project Setup

### Social Suit Setup

1. Install the shared library in the Social Suit virtual environment:

```bash
# Activate the Social Suit virtual environment
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install the shared library
cd /path/to/social_suit/shared
pip install -e .
```

2. Update imports in Social Suit to use the shared library components.

### Sparkr Setup

1. Install the shared library in the Sparkr virtual environment:

```bash
# Activate the Sparkr virtual environment
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install the shared library
cd /path/to/social_suit/shared
pip install -e .
```

2. Update imports in Sparkr to use the shared library components.

## Importing Shared Components

After installation, you can import the shared components in your code:

```python
# Authentication components
from shared.auth.jwt import JWTAuth
from shared.auth.security_middleware import SecurityMiddleware
from shared.auth.rate_limiter import RateLimiter

# Database components
from shared.database.sqlalchemy_base import get_db, get_async_session
from shared.database.redis_manager import RedisManager, redis_cache

# Utility components
from shared.utils.common import generate_uuid, generate_hash, json_serialize
from shared.utils.config import ConfigLoader
from shared.utils.logging_utils import setup_logging, RequestIdMiddleware
```

## Updating the Shared Library

When you make changes to the shared library:

1. If installed in development mode (-e), changes will be automatically available to both projects.

2. If installed normally, you'll need to reinstall the package:

```bash
cd /path/to/social_suit/shared
pip install .
```

## Version Control

The shared library is part of the Social Suit repository. When making changes:

1. Commit changes to the shared library along with any necessary updates to Social Suit.

2. When updating Sparkr to use the shared library, make sure to use the same version of the shared library that is compatible with your Sparkr version.

## Testing

To run tests for the shared library:

```bash
# Navigate to the shared library directory
cd /path/to/social_suit/shared

# Run tests
python -m unittest discover
```

## Troubleshooting

### Import Errors

If you encounter import errors:

1. Verify that the shared library is installed in your virtual environment:

```bash
pip list | grep shared
```

2. Check that your Python path includes the shared library:

```python
import sys
print(sys.path)
```

3. Try reinstalling the shared library:

```bash
pip uninstall shared
cd /path/to/social_suit/shared
pip install -e .
```

### Pydantic Version Compatibility

If you encounter Pydantic-related errors:

1. Check the Pydantic version in both projects:

```bash
pip show pydantic
```

2. Make sure both projects use compatible Pydantic versions. The shared library is designed to work with Pydantic v1.x.

### Other Issues

For other issues, check the logs and error messages. If you encounter bugs or have feature requests, please report them to the development team.