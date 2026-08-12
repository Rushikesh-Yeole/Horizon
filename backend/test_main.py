import pytest
from fastapi.testclient import TestClient
import main
from main import app
import contextvars
import ops

client = TestClient(app)

@pytest.mark.asyncio
async def test_metering_middleware_exposes_headers(monkeypatch):
    # Mock redis so the middleware doesn't fail
    class DummyRedis:
        async def get(self, key):
            return "100.0"
        async def set(self, key, value):
            pass
        async def incrbyfloat(self, key, value):
            return 100.0 + value

    monkeypatch.setattr(main, "_redis", DummyRedis())

    # Mock the endpoint so it costs something
    @app.get("/test-cost")
    async def test_cost():
        ops.current_request_cost.get()[0] += 0.05
        return {"ok": True}

    # Since app is already instantiated, we might need to just use client.get
    # Add the Origin header to trigger CORS
    response = client.get(
        "/test-cost",
        headers={
            "Origin": "http://localhost:5173",
            "x-demo-session-id": "test-session"
        }
    )

    # We expect the custom headers to be returned
    assert "x-credits-remaining" in response.headers or "X-Credits-Remaining" in response.headers
    assert "x-cost-this-run" in response.headers or "X-Cost-This-Run" in response.headers
    
    # We ALSO expect them to be exposed to the browser via CORS
    exposed = response.headers.get("access-control-expose-headers", "").lower()
    assert "x-credits-remaining" in exposed
    assert "x-cost-this-run" in exposed
