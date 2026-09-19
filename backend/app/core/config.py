import os
from pathlib import Path
from typing import Optional, Any, List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    PROJECT_NAME: str = "DocAudit AI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Asynchronous Document Audit & Extraction Engine"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment & Host
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # AI Providers & Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "120.0"))
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "auto") # auto, gemini, openai, ollama, mock
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    STORAGE_DIR: Path = BASE_DIR / "data" / "storage"
    DB_PATH: Path = BASE_DIR / "data" / "docaudit.db"
    
    # Limits & Parameters
    MAX_UPLOAD_SIZE_MB: int = 50
    CHUNK_SIZE: int = 800 # characters
    CHUNK_OVERLAP: int = 150 # characters
    RATE_LIMIT_PER_MINUTE: int = 120
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    CORS_ORIGIN_REGEX: Optional[str] = r"^https:\/\/.*(\.vercel\.app|\.onrender\.com)$"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                raw_list = json.loads(v)
            else:
                raw_list = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            raw_list = list(v)
        else:
            return v
        return [str(item).strip().rstrip("/") for item in raw_list if str(item).strip()]
    
    # Vector store type: "local" or "pgvector"
    VECTOR_STORE_TYPE: str = os.getenv("VECTOR_STORE_TYPE", "local")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'docaudit.db'}")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
(settings.BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
