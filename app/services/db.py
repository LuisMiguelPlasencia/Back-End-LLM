# Database connection pool and helpers using asyncpg
# Assumes DATABASE_URL is set in .env file
# Provides reusable connection pool for all database operations

import asyncpg
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv(override=True)

# Global connection pool
_pool = None

async def init_db():
    """Initialize the database connection pool based on environment"""
    global _pool
    
    current_env = os.getenv("ENVIRONMENT", "DEV").upper()
    if current_env == "PRO":
        database_url = os.getenv("DATABASE_URL_PRO")
    elif current_env == "DEV":
        database_url = os.getenv("DATABASE_URL_DEV")
    else:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(f"No connection URL found for environment: {current_env}")

    _pool = await asyncpg.create_pool(database_url, statement_cache_size=0)
    return _pool

async def close_db():
    """Close the database connection pool"""
    global _pool
    if _pool:
        await _pool.close()

@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool"""
    global _pool
    if not _pool:
        await init_db()
    
    async with _pool.acquire() as connection:
        yield connection

# Helper function for easy access
async def execute_query(query: str, *args):
    """Execute a query and return results"""
    async with get_db_connection() as conn:
        return await conn.fetch(query, *args)

async def execute_query_one(query: str, *args):
    """Execute a query and return single result"""
    async with get_db_connection() as conn:
        return await conn.fetchrow(query, *args)
