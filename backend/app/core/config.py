"""Application settings and configuration module.

This module defines the Settings class which uses pydantic-settings to load
environment variables from a .env file or the system environment.
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings class loaded from environment variables."""

    # Pydantic Settings configuration to specify env file path
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "InterviewPilot-AI API"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000

    # CORS configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "https://rag-placement-copilot-ebon.vercel.app"
    ]


    # PostgreSQL Database configuration
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "interviewpilot"

    # Qdrant Vector DB Configuration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Supabase configuration
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_KEY: str = "your-anon-public-key"
    SUPABASE_JWT_SECRET: str = "your-jwt-secret-for-offline-verification"
    SUPABASE_SERVICE_ROLE_KEY: str = "your-service-role-key"

    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_MODEL: str = "open-mistral-nemo"
    LLM_PROVIDER: str = "gemini"

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Constructs the SQLAlchemy database URI from components."""
        if self.DATABASE_URL:
            uri = self.DATABASE_URL
            if uri.startswith("postgres://"):
                uri = uri.replace("postgres://", "postgresql://", 1)
            return uri
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


# Global settings instance
settings = Settings()
