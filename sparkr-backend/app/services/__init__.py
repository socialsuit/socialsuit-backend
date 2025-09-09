"""Service package for business logic.

This package provides services that implement business logic and use repositories
for database access. Services are designed to be used with FastAPI's dependency
injection system.
"""

from app.services.user_service import UserService

# Export services
__all__ = ["UserService"]