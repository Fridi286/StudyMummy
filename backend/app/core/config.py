"""
Zentrale Konfiguration via Pydantic Settings.
Alle Werte können über Umgebungsvariablen oder .env überschrieben werden.
"""
from typing import ClassVar
from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
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
    secret_key: str = "super_secret_default_key"

    # LLM
    openai_api_key: str = "MISSING_KEY"
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3

    # HAW ICC Fallback
    haw_icc_api_key: str | None = None
    haw_icc_base_url: str = "https://llm.inf.haw-hamburg.de/v1"
    
    @model_validator(mode="after")
    def apply_haw_icc_fallback(self) -> "Settings":
        if self.openai_api_key == "MISSING_KEY" or not self.openai_api_key:
            if self.haw_icc_api_key:
                self.openai_api_key = self.haw_icc_api_key
                if not self.openai_base_url:
                    self.openai_base_url = self.haw_icc_base_url
        return self

    # RAG
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/studymummy"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
