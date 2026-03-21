# ---------------------------------------------------------------------------
# Database connection pool (asyncpg) — single source of truth
# ---------------------------------------------------------------------------
# Provides:
#   • Async connection pool with env-aware URL resolution
#   • Context-managed connections (get_connection)
#   • Convenience execute helpers that prevent leaked connections
#   • Transaction support via get_transaction()
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, List, Optional, Sequence

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level pool reference
# ---------------------------------------------------------------------------
_pool: Optional[asyncpg.Pool] = None

# ---------------------------------------------------------------------------
# Pool configuration (from centralised settings)
# ---------------------------------------------------------------------------
_MIN_POOL_SIZE = settings.db_pool_min
_MAX_POOL_SIZE = settings.db_pool_max
_POOL_MAX_INACTIVE_CONN_LIFETIME = 300.0


def _resolve_database_url() -> str:
    """Return the correct DATABASE_URL based on the ENVIRONMENT setting."""
    env = settings.environment.upper()
    url_map = {
        "PRO": settings.database_url_pro,
        "DEV": settings.database_url_dev,
    }
    database_url = url_map.get(env) or settings.database_url
    if not database_url:
        raise ValueError(
            f"No database connection URL found for environment '{env}'. "
            "Set DATABASE_URL_DEV, DATABASE_URL_PRO, or DATABASE_URL in your .env file."
        )
    return database_url


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

async def init_db() -> asyncpg.Pool:
    """Create and return the global connection pool.

    Safe to call multiple times — only the first invocation creates the pool.
    """
    global _pool
    if _pool is not None:
        return _pool

    database_url = _resolve_database_url()

    _pool = await asyncpg.create_pool(
        database_url,
        min_size=_MIN_POOL_SIZE,
        max_size=_MAX_POOL_SIZE,
        max_inactive_connection_lifetime=_POOL_MAX_INACTIVE_CONN_LIFETIME,
        statement_cache_size=0,  # disable prepared-statement cache for pgBouncer compat
    )
    logger.info(
        "Database pool initialised (min=%d, max=%d)",
        _MIN_POOL_SIZE,
        _MAX_POOL_SIZE,
    )
    return _pool


async def close_db() -> None:
    """Gracefully drain and close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed.")


def get_pool() -> asyncpg.Pool:
    """Return the live pool reference (raises if not initialised)."""
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. Call init_db() first "
            "(this normally happens automatically during application startup)."
        )
    return _pool


# ---------------------------------------------------------------------------
# Connection / transaction helpers
# ---------------------------------------------------------------------------

@asynccontextmanager
async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    """Acquire a connection from the pool (auto-released on exit)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_transaction() -> AsyncIterator[asyncpg.Connection]:
    """Acquire a connection *inside a transaction block*.

    Usage::

        async with get_transaction() as tx:
            await tx.execute("INSERT ...")
            await tx.execute("UPDATE ...")
        # COMMIT happens automatically; ROLLBACK on exception.
    """
    async with get_connection() as conn:
        async with conn.transaction():
            yield conn


# ---------------------------------------------------------------------------
# Query convenience wrappers
# ---------------------------------------------------------------------------

async def execute_query(query: str, *args: Any) -> List[asyncpg.Record]:
    """Execute *query* and return **all** rows."""
    async with get_connection() as conn:
        return await conn.fetch(query, *args)


async def execute_query_one(query: str, *args: Any) -> Optional[asyncpg.Record]:
    """Execute *query* and return a **single** row (or ``None``)."""
    async with get_connection() as conn:
        return await conn.fetchrow(query, *args)


async def execute_command(query: str, *args: Any) -> str:
    """Execute a DML statement and return the status string (e.g. ``'UPDATE 1'``)."""
    async with get_connection() as conn:
        return await conn.execute(query, *args)
