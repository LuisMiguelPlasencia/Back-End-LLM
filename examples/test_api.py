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

# Headers para autenticación (reemplazar con token real)
HEADERS = {
    "Authorization": "Bearer your-jwt-token-here",
    "Content-Type": "application/json"
}


def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    
    response = requests.get(f"{API_BASE}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_upload_audio():
    """Test audio upload endpoint"""
    print("🎵 Testing audio upload...")
    
    # Crear archivo de audio de prueba
    test_audio_path = Path("test_audio.wav")
    if not test_audio_path.exists():
        # Crear archivo de audio dummy
        with open(test_audio_path, "wb") as f:
            f.write(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
    
    files = {
        "file": ("test_audio.wav", open(test_audio_path, "rb"), "audio/wav")
    }
    data = {
        "language": "es"
    }
    
    response = requests.post(
        f"{API_BASE}/audio/upload",
        files=files,
        data=data,
        headers={"Authorization": HEADERS["Authorization"]}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Audio ID: {result['id']}")
        print(f"Filename: {result['filename']}")
        return result['id']
    else:
        print(f"Error: {response.text}")
        return None


def test_start_transcription(audio_id):
    """Test transcription start endpoint"""
    print(f"🎤 Testing transcription for audio {audio_id}...")
    
    response = requests.post(
        f"{API_BASE}/audio/{audio_id}/transcribe",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Task ID: {result['task_id']}")
        print(f"Transcription ID: {result['transcription_id']}")
        return result['transcription_id']
    else:
        print(f"Error: {response.text}")
        return None


def test_get_transcription(transcription_id):
    """Test get transcription endpoint"""
    print(f"📝 Testing get transcription {transcription_id}...")
    
    response = requests.get(
        f"{API_BASE}/audio/transcription/{transcription_id}",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Text: {result['text']}")
        print(f"Confidence: {result['confidence']}")
        return result
    else:
        print(f"Error: {response.text}")
        return None


def test_chat_completion(transcription_id):
    """Test chat completion endpoint"""
    print(f"💬 Testing chat completion for transcription {transcription_id}...")
    
    data = {
        "transcription_id": transcription_id,
        "message": "¿Qué dice el audio? Resúmelo en 2 líneas."
    }
    
    response = requests.post(
        f"{API_BASE}/chat/completion",
        json=data,
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result['message']}")
        print(f"Tokens used: {result['tokens_used']}")
        print(f"Model used: {result['model_used']}")
        return result
    else:
        print(f"Error: {response.text}")
        return None


def test_list_audios():
    """Test list audios endpoint"""
    print("📋 Testing list audios...")
    
    response = requests.get(
        f"{API_BASE}/audio/",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        audios = response.json()
        print(f"Found {len(audios)} audio files")
        for audio in audios:
            print(f"  - {audio['original_filename']} (ID: {audio['id']})")
        return audios
    else:
        print(f"Error: {response.text}")
        return None


def test_create_chat_session():
    """Test create chat session endpoint"""
    print("💭 Testing create chat session...")
    
    data = {
        "title": "Sesión de prueba"
    }
    
    response = requests.post(
        f"{API_BASE}/chat/sessions",
        json=data,
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Session ID: {result['id']}")
        print(f"Title: {result['title']}")
        return result['id']
    else:
        print(f"Error: {response.text}")
        return None


def test_add_message(session_id):
    """Test add message endpoint"""
    print(f"💬 Testing add message to session {session_id}...")
    
    data = {
        "content": "Hola, ¿cómo estás?",
        "role": "user"
    }
    
    response = requests.post(
        f"{API_BASE}/chat/sessions/{session_id}/messages",
        json=data,
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Message ID: {result['id']}")
        print(f"Content: {result['content']}")
        print(f"Role: {result['role']}")
        return result
    else:
        print(f"Error: {response.text}")
        return None


def main():
    """Run all API tests"""
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # Test health check
    test_health_check()
    
    # Test audio upload
    audio_id = test_upload_audio()
    
    if audio_id:
        # Test transcription
        transcription_id = test_start_transcription(audio_id)
        
        if transcription_id:
            # Wait a bit for transcription to complete
            import time
            print("⏳ Waiting for transcription to complete...")
            time.sleep(5)
            
            # Test get transcription
            transcription = test_get_transcription(transcription_id)
            
            if transcription and transcription['status'] == 'completed':
                # Test chat completion
                test_chat_completion(transcription_id)
    
    # Test list audios
    test_list_audios()
    
    # Test chat sessions
    session_id = test_create_chat_session()
    if session_id:
        test_add_message(session_id)
    
    print("=" * 50)
    print("✅ API tests completed!")


if __name__ == "__main__":
    main() 