#!/usr/bin/env python3
"""
Ejemplos de uso de la API Speech-to-Text
"""
import requests
import json
import os
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"




def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    
    response = requests.get(f"{API_BASE}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_upload_text():
    """Test text upload endpoint"""
    print("📝 Testing text upload...")
    
    data = {
        "title": "Test transcription",
        "content": "Este es un texto de prueba para verificar que el backend funciona correctamente.",
        "language": "es",
        "source": "upload"
    }
    
    response = requests.post(
        f"{API_BASE}/text/upload",
        data=data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Text ID: {result['id']}")
        print(f"Title: {result['title']}")
        return result['id']
    else:
        print(f"Error: {response.text}")
        return None





def test_get_text_entry(text_id):
    """Test get text entry endpoint"""
    print(f"📄 Testing get text entry {text_id}...")
    
    response = requests.get(f"{API_BASE}/text/{text_id}")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Title: {result['title']}")
        print(f"Content: {result['content']}")
        return result
    else:
        print(f"Error: {response.text}")
        return None


def test_list_text_entries():
    """Test list text entries endpoint"""
    print("📋 Testing list text entries...")
    
    response = requests.get(f"{API_BASE}/text/")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        entries = response.json()
        print(f"Found {len(entries)} text entries")
        for entry in entries:
            print(f"  - {entry['title']} (ID: {entry['id']})")
        return entries
    else:
        print(f"Error: {response.text}")
        return None


def main():
    """Run all API tests"""
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # Test health check
    test_health_check()
    
    # Test text upload
    text_id = test_upload_text()
    
    if text_id:
        # Test get text entry
        test_get_text_entry(text_id)
    
    # Test list text entries
    test_list_text_entries()
    
    print("=" * 50)
    print("✅ API tests completed!")


if __name__ == "__main__":
    main() 