import time
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
    _ollama_status_cache: Optional[Dict[str, Any]] = None
    _ollama_cache_time: float = 0.0
    _CACHE_TTL_SECONDS: float = 10.0

    @classmethod
    async def check_ollama_status(cls, force_refresh: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force_refresh and cls._ollama_status_cache is not None and (now - cls._ollama_cache_time < cls._CACHE_TTL_SECONDS):
            return cls._ollama_status_cache

        status = await OllamaProvider.check_connection()
        cls._ollama_status_cache = status
        cls._ollama_cache_time = now
        return status

    @classmethod
    def check_ollama_status_sync(cls, force_refresh: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force_refresh and cls._ollama_status_cache is not None and (now - cls._ollama_cache_time < cls._CACHE_TTL_SECONDS):
            return cls._ollama_status_cache

        status = OllamaProvider.check_connection_sync()
        cls._ollama_status_cache = status
        cls._ollama_cache_time = now
        return status

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> BaseLLMProvider:
        raw_requested = (provider_name or "").lower().strip()
        is_explicit = bool(raw_requested and raw_requested != "auto")
        target = raw_requested if is_explicit else settings.DEFAULT_LLM_PROVIDER.lower().strip()

        if is_explicit:
            if target == "gemini":
                if "gemini" not in cls._cached_providers:
                    cls._cached_providers["gemini"] = GeminiProvider()
                return cls._cached_providers["gemini"]
            elif target == "openai":
                if "openai" not in cls._cached_providers:
                    cls._cached_providers["openai"] = OpenAIProvider()
                return cls._cached_providers["openai"]
            elif target == "ollama":
                if "ollama" not in cls._cached_providers:
                    cls._cached_providers["ollama"] = OllamaProvider()
                return cls._cached_providers["ollama"]
            elif target == "mock":
                if "mock" not in cls._cached_providers:
                    cls._cached_providers["mock"] = MockProvider()
                return cls._cached_providers["mock"]

        # If user explicitly configured DEFAULT_LLM_PROVIDER in .env
        if target == "gemini" and settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
            if "gemini" not in cls._cached_providers:
                cls._cached_providers["gemini"] = GeminiProvider()
            return cls._cached_providers["gemini"]

        if target == "openai" and settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5:
            if "openai" not in cls._cached_providers:
                cls._cached_providers["openai"] = OpenAIProvider()
            return cls._cached_providers["openai"]

        if target == "ollama":
            status = cls.check_ollama_status_sync()
            if status.get("online") and status.get("model_installed"):
                if "ollama" not in cls._cached_providers:
                    cls._cached_providers["ollama"] = OllamaProvider()
                return cls._cached_providers["ollama"]
            logger.warning("DEFAULT_LLM_PROVIDER is 'ollama' but Ollama is not ready. Falling back to Mock.")
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

        # Check if Ollama is online and model ready in auto mode
        try:
            status = cls.check_ollama_status_sync()
            if status.get("online") and status.get("model_installed"):
                if "ollama" not in cls._cached_providers:
                    cls._cached_providers["ollama"] = OllamaProvider()
                return cls._cached_providers["ollama"]
        except Exception as e:
            logger.warning(f"Failed to check Ollama during auto selection: {e}")

        # Fallback to Mock provider for zero-friction local execution
        if "mock" not in cls._cached_providers:
            cls._cached_providers["mock"] = MockProvider()
        return cls._cached_providers["mock"]

    @classmethod
    def _build_provider_list(cls, ollama_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        ollama_online = bool(ollama_status.get("online", False))
        ollama_installed = bool(ollama_status.get("model_installed", False))
        ollama_available = ollama_online and ollama_installed
        ollama_model = getattr(settings, "OLLAMA_MODEL", "llama3")

        gemini_has_key = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)
        openai_has_key = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5)

        gemini_is_default = (settings.DEFAULT_LLM_PROVIDER == "gemini" and gemini_has_key) or (
            settings.DEFAULT_LLM_PROVIDER == "auto" and gemini_has_key
        )
        openai_is_default = (settings.DEFAULT_LLM_PROVIDER == "openai" and openai_has_key) or (
            settings.DEFAULT_LLM_PROVIDER == "auto" and not gemini_has_key and openai_has_key
        )
        ollama_is_default = (settings.DEFAULT_LLM_PROVIDER == "ollama" and ollama_available) or (
            settings.DEFAULT_LLM_PROVIDER == "auto" and not gemini_has_key and not openai_has_key and ollama_available
        )
        mock_is_default = not gemini_is_default and not openai_is_default and not ollama_is_default

        return [
            {
                "id": "gemini",
                "name": "Google Gemini (gemini-2.5-flash)",
                "available": gemini_has_key,
                "status_message": "Ready" if gemini_has_key else "API key required (set GEMINI_API_KEY)",
                "is_default": gemini_is_default
            },
            {
                "id": "openai",
                "name": "OpenAI (gpt-4o-mini)",
                "available": openai_has_key,
                "status_message": "Ready" if openai_has_key else "API key required (set OPENAI_API_KEY)",
                "is_default": openai_is_default
            },
            {
                "id": "ollama",
                "name": f"Ollama Local ({ollama_model})",
                "available": ollama_available,
                "online": ollama_online,
                "model_installed": ollama_installed,
                "status_message": ollama_status.get("message", "Ready" if ollama_available else "Not ready"),
                "is_default": ollama_is_default
            },
            {
                "id": "mock",
                "name": "DocAudit Deterministic Heuristic Engine (Offline / Local)",
                "available": True,
                "status_message": "Ready (Built-in offline engine)",
                "is_default": mock_is_default
            }
        ]

    @classmethod
    async def list_providers_async(cls) -> List[Dict[str, Any]]:
        """
        Asynchronously probes dynamic provider availability (e.g. pinging Ollama).
        """
        ollama_status = await cls.check_ollama_status()
        return cls._build_provider_list(ollama_status)

    @classmethod
    def list_providers(cls) -> List[Dict[str, Any]]:
        """
        Synchronous provider listing with fast cached status lookup.
        """
        ollama_status = cls.check_ollama_status_sync()
        return cls._build_provider_list(ollama_status)
