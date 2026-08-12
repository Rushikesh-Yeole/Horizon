import pytest
import asyncio
import json
from discover import _fetch_jd
from ops import log_llm_cost

class DummyUsage:
    @property
    def prompt_tokens(self):
        raise AttributeError("'NoneType' object has no attribute 'prompt_tokens'")

class DummyResponse:
    def __init__(self):
        self.usage = None
        self.choices = None

class DummyCompletions:
    async def create(self, **kwargs):
        return DummyResponse()

class DummyChat:
    def __init__(self):
        self.completions = DummyCompletions()

class DummyClient:
    def __init__(self):
        self.chat = DummyChat()

@pytest.mark.asyncio
async def test_fetch_jd_none_choices(monkeypatch, caplog):
    import discover
    import logging
    
    caplog.set_level(logging.WARNING)
    
    monkeypatch.setattr(discover, "_client", DummyClient())
    
    # We also mock TavilyClient so it doesn't do a real API call
    class DummyTavily:
        def __init__(self, api_key):
            pass
        def search(self, **kwargs):
            return {"results": [{"content": "dummy search result"}]}
    
    monkeypatch.setattr("tavily.TavilyClient", DummyTavily)
    
    jd_text, skills, from_cache = await discover._fetch_jd(None, "SWE", "Google", "Remote")
    
    # If the bug exists, it logs "JD fetch failed [Google]: 'NoneType' object is not subscriptable"
    assert "JD fetch failed" not in caplog.text
    assert jd_text == json.dumps({"skills": [], "resp": "JD unavailable."})
