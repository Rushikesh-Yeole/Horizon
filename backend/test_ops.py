import pytest
from ops import log_llm_cost

class DummyResponse:
    def __init__(self, usage):
        self.usage = usage

def test_log_llm_cost_handles_none_usage(capsys):
    resp = DummyResponse(usage=None)
    cost = log_llm_cost("test", "google/gemini-2.5-flash", resp)
    
    captured = capsys.readouterr()
    assert "[cost] test | google/gemini-2.5-flash | in=0 out=0" in captured.out
    assert "log failed" not in captured.out
    assert cost == 0
