#!/usr/bin/env python3
"""
Test script to verify backend integration
"""
import requests
import json

# Test backend endpoints
BACKEND_URL = "http://127.0.0.1:8000"
JOBFORGE_URL = "http://127.0.0.1:8001"

def test_backend_endpoints():
    """Test main backend endpoints"""
    print("Testing Backend Endpoints...")
    
    # Test MBTI questions endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/user/questions")
        if response.status_code == 200:
            print("✅ MBTI Questions endpoint working")
            questions = response.json().get('questions', [])
            print(f"   Found {len(questions)} questions")
        else:
            print(f"❌ MBTI Questions endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ MBTI Questions endpoint error: {e}")
    
    # Test login endpoint (should fail with invalid credentials)
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        if response.status_code == 401:
            print("✅ Login endpoint working (correctly rejecting invalid credentials)")
        else:
            print(f"❌ Login endpoint unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Login endpoint error: {e}")

def test_jobforge_endpoints():
    """Test jobForge endpoints"""
    print("\nTesting JobForge Endpoints...")
    
    # Test recommend endpoint
    try:
        response = requests.get(f"{JOBFORGE_URL}/recommend/x")
        if response.status_code == 200:
            print("✅ Recommend endpoint working")
            data = response.json()
            print(f"   Found {data.get('count', 0)} recommended jobs")
            if data.get('results'):
                job = data['results'][0]
                print(f"   Sample job: {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
        else:
            print(f"❌ Recommend endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Recommend endpoint error: {e}")
    
    # Test search endpoint
    try:
        response = requests.post(f"{JOBFORGE_URL}/search/x", json={
            "titles": ["Software Engineer"]
        })
        if response.status_code == 200:
            print("✅ Search endpoint working")
            data = response.json()
            print(f"   Found {data.get('count', 0)} search results")
        else:
            print(f"❌ Search endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")

def test_career_tree_endpoint():
    """Test career tree endpoint"""
    print("\nTesting Career Tree Endpoint...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/careertree/generate/x")
        if response.status_code == 200:
            print("✅ Career Tree endpoint working")
            data = response.json()
            if data.get('status') == 'ok':
                print("   Career tree generation successful")
            else:
                print(f"   Career tree response: {data}")
        else:
            print(f"❌ Career Tree endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Career Tree endpoint error: {e}")

if __name__ == "__main__":
    print("🔍 Testing Horizon Backend Integration")
    print("=" * 50)
    
    test_backend_endpoints()
    test_jobforge_endpoints()
    test_career_tree_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ Integration test completed!")
    print("\nTo start the servers:")
    print("Backend: cd backend && python -m uvicorn main:app --reload --port 8000")
    print("JobForge: cd jobForge && python -m uvicorn app.main:app --reload --port 8001")
    print("Frontend: cd frontend && npm start")

