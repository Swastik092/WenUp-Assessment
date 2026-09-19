import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    llm_api_key: str = "mock-api-key"
    llm_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Create a global settings object
settings = Settings()

def get_llm_client():
    from backend.services.llm_service import MockLLMService
    provider = settings.llm_provider.lower()

    if provider == "mock":
        return MockLLMService()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError(
                "LLM_PROVIDER is set to 'gemini' but GEMINI_API_KEY is not set. "
                "Add GEMINI_API_KEY to your .env file, or set LLM_PROVIDER=mock to run without a real LLM."
            )
        from backend.services.gemini_client import GeminiLLMService
        return GeminiLLMService(api_key=settings.gemini_api_key, model=settings.gemini_model)

    if provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("LLM_PROVIDER is set to 'groq' but GROQ_API_KEY is not set.")
        from backend.services.llm_service import GroqLLMService
        return GroqLLMService(api_key=settings.groq_api_key, model=settings.groq_model)

    raise RuntimeError(f"Unknown LLM_PROVIDER '{provider}'. Use 'mock', 'gemini', or 'groq'.")
