"""
Zentrale Konfiguration via Pydantic Settings.
Alle Werte können über Umgebungsvariablen oder .env überschrieben werden.
"""
from typing import ClassVar
from functools import lru_cache
from pydantic import Field, model_validator
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
    secret_key: str = "change_me_in_production_use_a_32_plus_byte_random_hex_string_here"

    # LLM
    openai_api_key: str = "MISSING_KEY"
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3
    openai_timeout_seconds: float = 20.0
    openai_max_retries: int = 0

    # Agent workflow
    agent_review_enabled: bool = True
    agent_max_coordination_rounds: int = Field(default=2, ge=1, le=4)

    # HAW ICC Fallback
    haw_icc_api_key: str | None = None
    haw_icc_base_url: str = "https://llm.inf.haw-hamburg.de/v1"

    _insecure_secret_keys: ClassVar[set[str]] = {
        "change_me_in_production_use_a_32_plus_byte_random_hex_string_here",
        "replace-with-a-random-32-byte-secret",
        "development-only-change-me",
    }
    
    @model_validator(mode="after")
    def apply_haw_icc_fallback(self) -> "Settings":
        if self.app_env.casefold() == "production" and (
            len(self.secret_key) < 32 or self.secret_key in self._insecure_secret_keys
        ):
            raise ValueError(
                "SECRET_KEY must be a non-placeholder value of at least 32 characters in production"
            )
        if self.openai_api_key == "MISSING_KEY" or not self.openai_api_key:
            if self.haw_icc_api_key:
                self.openai_api_key = self.haw_icc_api_key
                if not self.openai_base_url:
                    self.openai_base_url = self.haw_icc_base_url
        return self

    # RAG
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "text-embedding-3-small"

    @property
    def rag_embeddings_enabled(self) -> bool:
        return bool(self.embedding_model.strip())

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/studymummy"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
