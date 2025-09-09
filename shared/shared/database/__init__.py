"""Database utilities for shared projects.

This module provides common database functionality including:
- Connection management
- Session management
- Repository pattern implementation
- Pagination utilities
- Transaction management
"""

# Import key components to make them available when importing the database module
from shared.database.pagination import paginate_query, Page
from shared.database.connection import get_db_session, create_db_engine
from shared.database.repository import BaseRepository, transaction, get_repository
from shared.database.session import DatabaseSessionManager, init_models