import warnings
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

# Import from shared package
from shared.database.connection import create_db_engine, get_db_session

# Create async engine for PostgreSQL
async_engine = create_db_engine(
    settings.DB_URL,
    echo=settings.DEBUG,
    future=True
)

warnings.warn(
    "Direct use of async_engine is deprecated. Use shared.database.connection.create_db_engine instead.",
    DeprecationWarning,
    stacklevel=2
)

# Create async session factory using shared package
async_session_factory = get_db_session(async_engine)

warnings.warn(
    "Direct use of async_session_factory is deprecated. Use shared.database.connection.get_db_session instead.",
    DeprecationWarning,
    stacklevel=2
)

# Add this line to create an alias for async_session_factory
async_session_maker = async_session_factory


async def init_db():
    """Initialize database by creating all tables"""
    warnings.warn(
        "This function is deprecated. Consider using shared.database.connection functions instead.",
        DeprecationWarning,
        stacklevel=2
    )
    async with async_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for getting async session"""
    warnings.warn(
        "This function is deprecated. Use shared.database.connection.get_db_session instead.",
        DeprecationWarning,
        stacklevel=2
    )
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()