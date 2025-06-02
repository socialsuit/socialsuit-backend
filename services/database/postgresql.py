import asyncpg
import os
from contextlib import asynccontextmanager
import asyncio
from typing import AsyncGenerator, Optional

# Environment variables (with defaults for local development)
SUPABASE_URL = os.getenv("SUPABASE_URL", "db.project.supabase.co")
SUPABASE_DB = os.getenv("SUPABASE_DB", "postgres")
SUPABASE_USER = os.getenv("SUPABASE_USER", "postgres")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "your_password")
MAX_RETRIES = 3  # Max connection attempts
RETRY_DELAY = 1  # Seconds between retries

# Global connection pool
_pool: Optional[asyncpg.pool.Pool] = None

async def init_db_pool() -> None:
    """Initialize the connection pool with retry logic"""
    global _pool
    for attempt in range(MAX_RETRIES):
        try:
            _pool = await asyncpg.create_pool(
                host=SUPABASE_URL,
                database=SUPABASE_DB,
                user=SUPABASE_USER,
                password=SUPABASE_PASSWORD,
                min_size=2,
                max_size=10,
                command_timeout=30,  # Query timeout (seconds)
                connect_timeout=10,  # Connection timeout
                max_inactive_connection_lifetime=300  # Close idle connections
            )
            print("✅ Database pool initialized")
            return
        except (asyncpg.PostgresError, OSError) as e:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Failed to connect to DB after {MAX_RETRIES} attempts") from e
            print(f"⚠️ Connection failed (attempt {attempt + 1}): {e}")
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))

@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection with automatic cleanup"""
    if _pool is None:
        await init_db_pool()
    
    try:
        async with _pool.acquire() as conn:
            # Set a per-connection timeout
            await conn.execute("SET statement_timeout = 15000")  # 15 seconds
            yield conn
    except asyncpg.PostgresConnectionError as e:
        print(f"🚨 Connection error: {e}")
        raise
    except asyncpg.QueryCanceledError:
        print("⏱️ Query timeout exceeded")
        raise
    except Exception as e:
        print(f"❌ Unexpected DB error: {e}")
        raise

async def close_db_pool() -> None:
    """Cleanly close all connections"""
    if _pool:
        await _pool.close()
        print("🔌 Database pool closed")

# FastAPI lifespan example
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db_pool()

@app.on_event("shutdown")
async def shutdown():
    await close_db_pool()

@app.get("/users")
async def get_users():
    async with get_db_connection() as conn:
        return await conn.fetch("SELECT * FROM users LIMIT 100")