#!/usr/bin/env python3
"""
Setup script for Supabase integration
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_supabase
from app.config import settings


def setup_storage_bucket():
    """Create storage bucket for audio files"""
    try:
        supabase = get_supabase()
        
        # Create storage bucket
        bucket_name = "audio-files"
        bucket_config = {
            "name": bucket_name,
            "public": False,
            "allowed_mime_types": ["audio/*"],
            "file_size_limit": settings.max_file_size
        }
        
        # Note: This would require Supabase admin API
        # For now, create the bucket manually in Supabase dashboard
        print(f"📦 Please create storage bucket '{bucket_name}' manually in Supabase dashboard")
        print(f"   - Name: {bucket_name}")
        print(f"   - Public: False")
        print(f"   - Allowed MIME types: audio/*")
        print(f"   - File size limit: {settings.max_file_size} bytes")
        
    except Exception as e:
        print(f"❌ Error setting up storage: {e}")


def setup_database_policies():
    """Setup Row Level Security (RLS) policies"""
    print("🔐 Setting up database policies...")
    print("   Please run the following SQL in your Supabase SQL editor:")
    print()
    print("-- Enable RLS on all tables")
    print("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    print("ALTER TABLE audios ENABLE ROW LEVEL SECURITY;")
    print("ALTER TABLE transcriptions ENABLE ROW LEVEL SECURITY;")
    print("ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;")
    print("ALTER TABLE messages ENABLE ROW LEVEL SECURITY;")
    print()
    print("-- Users can only access their own data")
    print("CREATE POLICY \"Users can view own profile\" ON users")
    print("  FOR SELECT USING (auth.uid()::text = supabase_id);")
    print()
    print("CREATE POLICY \"Users can view own audios\" ON audios")
    print("  FOR ALL USING (auth.uid()::text = (SELECT supabase_id FROM users WHERE id = user_id));")
    print()
    print("CREATE POLICY \"Users can view own transcriptions\" ON transcriptions")
    print("  FOR ALL USING (audio_id IN (SELECT id FROM audios WHERE user_id = (SELECT id FROM users WHERE supabase_id = auth.uid()::text)));")
    print()
    print("CREATE POLICY \"Users can manage own chat sessions\" ON chat_sessions")
    print("  FOR ALL USING (auth.uid()::text = (SELECT supabase_id FROM users WHERE id = user_id));")
    print()
    print("CREATE POLICY \"Users can manage own messages\" ON messages")
    print("  FOR ALL USING (chat_session_id IN (SELECT id FROM chat_sessions WHERE user_id = (SELECT id FROM users WHERE supabase_id = auth.uid()::text)));")


def main():
    """Setup Supabase integration"""
    print("🔧 Setting up Supabase integration...")
    print()
    
    # Check configuration
    print("📋 Configuration check:")
    print(f"   Supabase URL: {settings.supabase_url}")
    print(f"   Supabase Key: {'✅ Set' if settings.supabase_key else '❌ Not set'}")
    print(f"   Service Key: {'✅ Set' if settings.supabase_service_key else '❌ Not set'}")
    print()
    
    if not settings.supabase_key or not settings.supabase_service_key:
        print("❌ Please set SUPABASE_KEY and SUPABASE_SERVICE_KEY in your .env file")
        return
    
    # Setup storage
    setup_storage_bucket()
    print()
    
    # Setup database policies
    setup_database_policies()
    print()
    
    print("✅ Supabase setup instructions completed!")
    print("   Next steps:")
    print("   1. Create the storage bucket in Supabase dashboard")
    print("   2. Run the SQL policies in Supabase SQL editor")
    print("   3. Test the connection with: python -m app.main")


if __name__ == "__main__":
    main() 