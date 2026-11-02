"""Settings, loaded once. Every value has a safe default so the API boots with
an empty .env — which is exactly how it behaves in CI and on a fresh clone."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_DIR = REPO_ROOT / "contracts" / "fixtures"
DATA_DIR = REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: str = "dev"
    cors_origins: str = "http://localhost:3000"

    # Database. Empty means "fixture mode": the API still serves every read
    # endpoint from contracts/fixtures so the frontend has something to talk to.
    database_url: str = ""
    direct_url: str = ""

    # LLM
    llm_provider: str = "groq"
    llm_fallback: str = "gemini"
    llm_timeout_s: float = 25.0
    gemini_api_key: str = ""
    gemini_thinking: str = "auto"   # off = send thinkingBudget 0 (Gemini can spend 45 s thinking)
    gemini_model: str = "auto"   # "auto" = ask the API which models the key can call
    groq_api_key: str = ""
    groq_model: str = "auto"
    llm_cache_version: int = 1

    max_upload_mb: int = 5

    # Auth proper lands later. Until then, which profile owns the data:
    # empty + exactly one profile in the database => that one, and the response
    # says `user_source: single_profile` so nobody mistakes it for a real session.
    demo_user_id: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url.strip())

    @property
    def llm_configured(self) -> bool:
        return bool(self.gemini_api_key or self.groq_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
