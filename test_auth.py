#!/usr/bin/env python3
"""
Test script for API key authentication middleware.
"""

import os
import signal
import subprocess
import sys
import time

import requests


def test_auth():
    """Test API key authentication."""

    # Set environment variables
    os.environ['API_KEYS'] = 'test-key-123,another-key-456'
    os.environ['API_KEY_REQUIRED'] = 'true'
    os.environ['DEBUG'] = 'true'

    print("🚀 Testing API Key Authentication")
    print("=" * 50)

    # Start server in background
    print("📡 Starting server...")
    server_process = subprocess.Popen([
        'uvicorn', 'main:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--log-level', 'info'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to start
    time.sleep(5)

    base_url = "http://localhost:8000"

    try:
        # Test 1: Health endpoint (should be exempt)
        print("\n1️⃣ Testing health endpoint (exempt)...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health endpoint accessible")
        else:
            print(f"   ❌ Health endpoint failed: {response.text}")

        # Test 2: Root endpoint without API key (should fail)
        print("\n2️⃣ Testing root endpoint without API key...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Authentication required (expected)")
        else:
            print(f"   ❌ Unexpected status: {response.text}")

        # Test 3: Root endpoint with valid API key (should succeed)
        print("\n3️⃣ Testing root endpoint with valid API key...")
        headers = {"Authorization": "Bearer test-key-123"}
        response = requests.get(f"{base_url}/", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Authentication successful: {data.get('platform')}")
        else:
            print(f"   ❌ Authentication failed: {response.text}")

        # Test 4: Root endpoint with invalid API key (should fail)
        print("\n4️⃣ Testing root endpoint with invalid API key...")
        headers = {"Authorization": "Bearer invalid-key"}
        response = requests.get(f"{base_url}/", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Invalid key rejected (expected)")
        else:
            print(f"   ❌ Unexpected status: {response.text}")

        # Test 5: API key in query parameter
        print("\n5️⃣ Testing API key in query parameter...")
        response = requests.get(f"{base_url}/?api_key=test-key-123", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Query parameter authentication works")
        else:
            print(f"   ❌ Query parameter auth failed: {response.text}")

        print("\n🎉 Authentication tests completed!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    finally:
        # Stop server
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_auth()