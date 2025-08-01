#!/usr/bin/env python3
"""
Startup script for Celery worker
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.tasks import celery_app


def main():
    """Start the Celery worker"""
    print("🔄 Starting Celery worker...")
    print("📋 Available tasks:")
    print("   - transcribe_audio")
    print("   - generate_llm_response")
    print("   - cleanup_failed_transcriptions")
    
    # Start Celery worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2"
    ])


if __name__ == "__main__":
    main() 