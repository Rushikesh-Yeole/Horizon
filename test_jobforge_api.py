#!/usr/bin/env python3
"""
Quick test script to verify JobForge API endpoints
"""
import requests
import json

JOBFORGE_URL = "http://127.0.0.1:8001"

def test_recommend_endpoint():
    """Test the recommend endpoint"""
    print("Testing /recommend/x endpoint...")
    try:
        response = requests.get(f"{JOBFORGE_URL}/recommend/x")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"✅ Recommend endpoint working - Found {data.get('count', 0)} jobs")
        else:
            print(f"❌ Recommend endpoint failed: {response.text}")
    except Exception as e:
        print(f"❌ Recommend endpoint error: {e}")

def test_search_endpoint():
    """Test the search endpoint"""
    print("\nTesting /search/x endpoint...")
    try:
        payload = {
            "titles": ["Software Engineer"],
            "top_k": 2,
            "min_relevance": 40
        }
        response = requests.post(f"{JOBFORGE_URL}/search/x", json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"✅ Search endpoint working - Found {data.get('count', 0)} jobs")
        else:
            print(f"❌ Search endpoint failed: {response.text}")
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")

if __name__ == "__main__":
    print("🔍 Testing JobForge API Endpoints")
    print("=" * 50)
    
    test_recommend_endpoint()
    test_search_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ API test completed!")

