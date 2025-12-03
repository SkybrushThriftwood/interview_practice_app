import pytest  # noqa: F401
from modules.utils import get_openai_settings, openai_call
from modules import utils

def test_get_openai_settings_defaults(monkeypatch):
    
    settings = get_openai_settings()
    assert "model" in settings
    assert "temperature" in settings
    assert settings["temperature"] == 0.2

def test_openai_call(monkeypatch):
    # Mock the _call_openai function
    
    monkeypatch.setattr(utils, "_call_openai", lambda **kwargs: "Mock response")
    
    response = openai_call("system instructions", "prompt text")
    assert response == "Mock response"
