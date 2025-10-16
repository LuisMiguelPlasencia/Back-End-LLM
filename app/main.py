# FastAPI application main entry point
# Creates and configures the FastAPI app with all routes
# Exports app for uvicorn: uvicorn app.main:app --reload

from fastapi import FastAPI
from contextlib import asynccontextmanager
from .services.db import init_db, close_db
from .routers import auth, read, insert

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

# Create FastAPI application
app = FastAPI(
    title="Conversa API",
    description="REST API for conversation management with courses and messaging",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(auth.router)
app.include_router(read.router)
app.include_router(insert.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Conversa API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "conversa-api",
        "version": "1.0.0"
    }