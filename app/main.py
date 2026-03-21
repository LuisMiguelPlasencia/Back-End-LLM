# ---------------------------------------------------------------------------
# Conversa API — Application entry point
# ---------------------------------------------------------------------------
# Creates the FastAPI application with:
#   • Async DB pool lifecycle (startup / shutdown)
#   • CORS middleware (configurable via CORS_ORIGINS env var)
#   • Request-ID injection for traceability
#   • Global exception handlers for consistent error envelopes
#   • All routers mounted under versioned prefixes where appropriate
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
import time
import uuid

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.services.db import close_db, init_db
from app.utils.exceptions import register_exception_handlers
from app.routers import (
    auth,
    insert,
    landing_page_assistant,
    payments,
    read,
    realtime_router,
    upload,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("conversa")


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application-wide resources."""
    logger.info("Starting Conversa API [env=%s]", settings.environment)
    await init_db()
    yield
    await close_db()
    logger.info("Conversa API shut down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Conversa API",
    description="Backend REST API for the Conversa conversation-training platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Request-ID + latency logging
class RequestContextMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID header and log request latency."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s → %d (%.1f ms) [rid=%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response


app.add_middleware(RequestContextMiddleware)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(read.router)
app.include_router(insert.router)
app.include_router(upload.router)
app.include_router(realtime_router.router)
app.include_router(payments.router)
app.include_router(landing_page_assistant.router)


# ---------------------------------------------------------------------------
# Health-check endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root():
    return {"message": "Conversa API is running", "status": "healthy"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "conversa-api",
        "version": "2.0.0",
        "environment": settings.environment,
    }
