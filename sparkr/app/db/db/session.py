from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from sparkr.app.core.config import settings

# Create async engine for PostgreSQL
async_engine = create_async_engine(
    settings.DB_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
async_session_factory = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Add this line to create an alias for async_session_factory
async_session_maker = async_session_factory


async def init_db():
    """Initialize database by creating all tables"""
    async with async_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for getting async session"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()