from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .services.db import init_db, close_db
from .routers import auth, read, insert, realtime_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    await init_db()
    yield
    await close_db()

# Create FastAPI app
app = FastAPI(
    title="Conversa API",
    description="REST API for conversation management with courses and messaging",
    version="1.0.0",
    lifespan=lifespan
)

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your frontend origin(s), e.g. ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # or ["GET", "POST", "OPTIONS"]
    allow_headers=["*"],  # or specify headers you expect, e.g. ["Content-Type", "Authorization"]
)

# Routers
app.include_router(auth.router)
app.include_router(read.router)
app.include_router(insert.router)
app.include_router(realtime_router.router)


@app.get("/")
async def root():
    return {"message": "Conversa API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "conversa-api",
        "version": "1.0.0"
    }

