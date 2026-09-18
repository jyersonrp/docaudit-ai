import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.services.ai.base import BaseLLMProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.mock_provider import MockProvider

logger = logging.getLogger(__name__)

class LLMFactory:
    _cached_providers: Dict[str, BaseLLMProvider] = {}

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> BaseLLMProvider:
        requested = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()

        if requested == "gemini":
            if "gemini" not in cls._cached_providers:
                cls._cached_providers["gemini"] = GeminiProvider()
            return cls._cached_providers["gemini"]

        if requested == "openai":
            if "openai" not in cls._cached_providers:
                cls._cached_providers["openai"] = OpenAIProvider()
            return cls._cached_providers["openai"]

        if requested == "ollama":
            if "ollama" not in cls._cached_providers:
                cls._cached_providers["ollama"] = OllamaProvider()
            return cls._cached_providers["ollama"]

        if requested == "mock":
            if "mock" not in cls._cached_providers:
                cls._cached_providers["mock"] = MockProvider()
            return cls._cached_providers["mock"]

        # AUTO resolution strategy
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
            try:
                if "gemini" not in cls._cached_providers:
                    cls._cached_providers["gemini"] = GeminiProvider()
                return cls._cached_providers["gemini"]
            except Exception as e:
                logger.warning(f"Failed to auto-select Gemini: {e}")

        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5:
            try:
                if "openai" not in cls._cached_providers:
                    cls._cached_providers["openai"] = OpenAIProvider()
                return cls._cached_providers["openai"]
            except Exception as e:
                logger.warning(f"Failed to auto-select OpenAI: {e}")

        # Fallback to Mock provider for zero-friction local execution
        if "mock" not in cls._cached_providers:
            cls._cached_providers["mock"] = MockProvider()
        return cls._cached_providers["mock"]

    @classmethod
    def list_providers(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": "gemini",
                "name": "Google Gemini (gemini-2.5-flash)",
                "available": bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5),
                "is_default": settings.DEFAULT_LLM_PROVIDER == "gemini" or (settings.DEFAULT_LLM_PROVIDER == "auto" and bool(settings.GEMINI_API_KEY))
            },
            {
                "id": "openai",
                "name": "OpenAI (gpt-4o-mini)",
                "available": bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5),
                "is_default": settings.DEFAULT_LLM_PROVIDER == "openai"
            },
            {
                "id": "ollama",
                "name": "Ollama Local (llama3)",
                "available": True,
                "is_default": settings.DEFAULT_LLM_PROVIDER == "ollama"
            },
            {
                "id": "mock",
                "name": "DocAudit Deterministic Heuristic Engine (Offline / Local)",
                "available": True,
                "is_default": not bool(settings.GEMINI_API_KEY) and not bool(settings.OPENAI_API_KEY) and settings.DEFAULT_LLM_PROVIDER in ["auto", "mock"]
            }
        ]
