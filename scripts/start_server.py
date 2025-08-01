#!/usr/bin/env python3
"""
Startup script for the Speech-to-Text Backend API
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings


def main():
    """Start the FastAPI server"""
    print("🚀 Starting Speech-to-Text Backend API...")
    print(f"📁 Environment: {settings.environment}")
    print(f"🐛 Debug mode: {settings.debug}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main() 