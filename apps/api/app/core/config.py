"""
COGNARC — Application Configuration
apps/api/app/core/config.py

Pydantic Settings — all config from environment variables.
§20: Never hardcode secrets. All values from env.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────
    APP_NAME: str = "cognarc"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── Supabase ──────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_PROJECT_ID: str = ""

    # ── MongoDB ───────────────────────────────────────────────
    MONGODB_URL: str = ""
    MONGODB_DB_NAME: str = "cognarc"

    # ── Groq ──────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL_QUEST: str = "llama3-70b-8192"
    GROQ_MODEL_PLANNER: str = "mixtral-8x7b-32768"

    # ── Redis ─────────────────────────────────────────────────
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""
    REDIS_URL: str = ""

    # ── Observability ─────────────────────────────────────────
    SENTRY_DSN: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

    # ── Computed Properties ───────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton. Import this, not Settings()."""
    return Settings()


# Module-level singleton for convenience
settings: Settings = get_settings()
