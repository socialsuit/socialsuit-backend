"""Repository package for database access.

This package provides repositories for database access using the repository pattern.
Repositories abstract database operations and provide a clean interface for services.
"""

from app.repositories.user_repository import UserRepository

# Export repositories
__all__ = ["UserRepository"]