#!/usr/bin/env python3
"""
Test script to verify CORS configuration
"""

import requests
import json

def test_cors():
    """Test CORS configuration"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing CORS configuration...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        print(f"   CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 2: OPTIONS request (preflight)
    try:
        headers = {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{base_url}/api/v1/chat/stream", headers=headers)
        print(f"✅ OPTIONS request: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ OPTIONS request failed: {e}")
    
    # Test 3: POST request
    try:
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:5173'
        }
        data = {
            "query": "Hello, test message",
            "conversation_id": "test-123",
            "hint": None
        }
        response = requests.post(f"{base_url}/api/v1/chat/stream", 
                               headers=headers, 
                               json=data,
                               timeout=5)
        print(f"✅ POST request: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ POST request failed: {e}")

if __name__ == "__main__":
    test_cors()
