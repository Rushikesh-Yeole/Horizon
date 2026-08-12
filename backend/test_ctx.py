import asyncio
import contextvars
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

app = FastAPI()
cost_var = contextvars.ContextVar("cost", default=None)

@app.middleware("http")
async def test_mid(request: Request, call_next):
    cost_var.set([0.0])
    res = await call_next(request)
    cost = cost_var.get()[0]
    res.headers["x-cost"] = str(cost)
    return res

@app.get("/")
async def root():
    cost_var.get()[0] += 5.0
    return {"ok": True}

def test_contextvar():
    client = TestClient(app)
    res = client.get("/")
    print("Cost header:", res.headers.get("x-cost"))
    assert res.headers.get("x-cost") == "5.0"

if __name__ == "__main__":
    test_contextvar()
