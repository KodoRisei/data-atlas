from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "DataAtlas"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # ── Catalog database ──────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://atlas:atlas@localhost:5432/data_atlas"
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── AI provider ───────────────────────────────────────────────────────────
    ai_provider: Literal["openai", "anthropic", "ollama"] = "openai"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # ── Ingestion ─────────────────────────────────────────────────────────────
    target_db_url: str = ""

    # ── Performance ───────────────────────────────────────────────────────────
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
