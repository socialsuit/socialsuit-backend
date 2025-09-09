from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Create a base class for declarative models
Base = declarative_base()

# Synchronous database session setup
def create_sync_engine(database_url: str, echo: bool = False):
    """Create a synchronous SQLAlchemy engine"""
    return create_engine(database_url, echo=echo)

def create_sync_session_factory(engine):
    """Create a synchronous session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_sync_db(session_local):
    """Dependency for getting synchronous database session"""
    db = session_local()
    try:
        yield db
    finally:
        db.close()
        
def get_sync_db_session(session_local):
    """Get a synchronous database session"""
    return session_local()

# Asynchronous database session setup
def create_async_engine_factory(database_url: str, echo: bool = False):
    """Create an asynchronous SQLAlchemy engine"""
    return create_async_engine(
        database_url,
        echo=echo,
        future=True,
    )

def create_async_session_factory(engine):
    """Create an asynchronous session factory"""
    return sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

async def get_async_session(session_factory):
    """Dependency for getting asynchronous database session"""
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()