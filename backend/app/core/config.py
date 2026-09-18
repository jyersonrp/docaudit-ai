import os
from pathlib import Path
from typing import Optional
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
    
    # Vector store type: "local" or "pgvector"
    VECTOR_STORE_TYPE: str = os.getenv("VECTOR_STORE_TYPE", "local")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'docaudit.db'}")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
(settings.BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
