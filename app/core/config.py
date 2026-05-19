"""
Zentrale Konfiguration via Pydantic Settings.
Alle Werte können über Umgebungsvariablen oder .env überschrieben werden.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "StudyMummy API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "INFO"

    # LLM
    openai_api_key: str = "MISSING_KEY"
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3

    # RAG
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "text-embedding-3-small"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
