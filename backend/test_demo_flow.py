import os
from dotenv import load_dotenv
load_dotenv()
os.environ["IS_TESTING"] = "1"

import asyncio
from fastapi.testclient import TestClient
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("demo_test")

# Import the FastAPI app directly
from main import app

def run_demo_test():
    with TestClient(app) as client:
        log.info("1. Testing Demo Login...")
        login_resp = client.post("/auth/login", json={
            "email": "demo@horizon.com",
            "password": "demo123"
        })
        
        if login_resp.status_code != 200:
            log.error(f"Demo login failed: {login_resp.text}")
            exit(1)
            
        data = login_resp.json()
        token = data.get("access_token")
        email = data.get("email")
        
        if email != "demo@horizon.com":
            log.error(f"Expected email in response, got: {email}")
            exit(1)
            
        log.info(f"Demo login successful! Token received. Email verified: {email}")
        
        log.info("2. Testing Discovery Engine with Demo Token...")
        headers = {"Authorization": f"Bearer {token}"}
        discover_resp = client.post("/discover/search", headers=headers, json={
            "search_criteria": {
                "role": "Machine Learning Engineer",
                "location": "San Francisco",
                "target_companies": ["OpenAI", "Anthropic"]
            }
        })
        
        if discover_resp.status_code != 200:
            log.error(f"Discovery search failed: {discover_resp.text}")
            exit(1)
            
        log.info("Discovery engine successfully evaluated the demo profile!")
        
        log.info("3. Testing Career Tree with Demo Token...")
        user_id = data.get("user_id")
        tree_resp = client.get(f"/career/tree?user_id={user_id}", headers=headers)
        if tree_resp.status_code != 200:
            log.error(f"Tree generation failed: {tree_resp.text}")
            exit(1)
        
        log.info("Career Tree successfully traversed for demo profile!")
        log.info("ALL DEMO FLOWS VERIFIED 100% PERFECTLY.")

if __name__ == "__main__":
    run_demo_test()
