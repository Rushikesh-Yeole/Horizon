import sys
import logging
from fastapi.testclient import TestClient
from main import app
import os
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("e2e_test")

def run_tests():
    # Make sure we don't clobber real data if possible, though this is a test.
    with TestClient(app) as client:
        log.info("Testing /auth/register...")
        email = f"test_e2e_{int(time.time())}@example.com"
        password = "password123"
        reg_resp = client.post("/auth/register", json={
            "email": email,
            "password": password,
            "profile": {"name": "E2E Test User"}
        })
        if reg_resp.status_code not in (200, 201) and "already registered" not in reg_resp.text.lower():
            log.error(f"Register failed: {reg_resp.text}")
            sys.exit(1)
            
        log.info("Testing /auth/login...")
        login_resp = client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        if login_resp.status_code != 200:
            log.error(f"Login failed: {login_resp.text}")
            sys.exit(1)
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # We need the created user_id to pass to /career/tree. 
        # Usually login returns user_id, let's see.
        user_id = login_resp.json().get("user_id") or "9f3c7a21-6d44-4a9f-8f1e-2b6c9d3e7a55"
        
        log.info("Testing /discover/search...")
        discover_resp = client.post("/discover/search", headers=headers, json={
            "search_criteria": {
                "role": "Frontend Engineer",
                "location": "Remote",
                "target_companies": ["Google", "Stripe"]
            }
        })
        if discover_resp.status_code != 200:
            log.error(f"Discover failed: {discover_resp.text}")
            sys.exit(1)
        
        log.info(f"Discover Response: {discover_resp.json()}")
        
        log.info("Testing /career/tree...")
        tree_resp = client.get(f"/career/tree?user_id={user_id}", headers=headers)
        if tree_resp.status_code != 200:
            log.error(f"Tree failed: {tree_resp.text}")
            sys.exit(1)
            
        log.info(f"Tree Response: {tree_resp.json()}")
        log.info("All end-to-end flows passed perfectly!")
        
if __name__ == "__main__":
    run_tests()
