import pytest
import unittest.mock
from backend.config import get_llm_client, Settings

def test_config_mock():
    # If provider is mock, it succeeds regardless of gemini key
    with unittest.mock.patch("backend.config.settings", Settings(llm_provider="mock", gemini_api_key=None)):
        client = get_llm_client()
        from backend.services.llm_service import MockLLMService
        assert isinstance(client, MockLLMService)

def test_config_gemini_missing_key():
    # If provider is gemini but no key is set, it fails fast
    with unittest.mock.patch("backend.config.settings", Settings(llm_provider="gemini", gemini_api_key=None)):
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not set"):
            get_llm_client()

def test_config_gemini_success():
    # If provider is gemini and key is set, it returns GeminiLLMService
    with unittest.mock.patch("backend.config.settings", Settings(llm_provider="gemini", gemini_api_key="real-key")):
        with unittest.mock.patch("backend.services.gemini_client.genai"):
            client = get_llm_client()
            from backend.services.gemini_client import GeminiLLMService
            assert isinstance(client, GeminiLLMService)
