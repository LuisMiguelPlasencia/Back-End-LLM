# ---------------------------------------------------------------------------
# Application-wide configuration — loaded once at import time
# ---------------------------------------------------------------------------
# Uses pydantic-settings for typed, validated environment variables.
# All secrets are read from `.env`; never hard-coded.
# ---------------------------------------------------------------------------

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised, validated application settings."""

    # -- Environment ----------------------------------------------------------
    environment: str = Field(default="DEV", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # -- Database (resolved in db.py via DATABASE_URL_* env vars) -------------
    database_url_dev: Optional[str] = Field(default=None, alias="DATABASE_URL_DEV")
    database_url_pro: Optional[str] = Field(default=None, alias="DATABASE_URL_PRO")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    db_pool_min: int = Field(default=5, alias="DB_POOL_MIN")
    db_pool_max: int = Field(default=20, alias="DB_POOL_MAX")

    # -- OpenAI ---------------------------------------------------------------
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_default_model: str = Field(
        default="gpt-4.1-nano-2025-04-14", alias="OPENAI_DEFAULT_MODEL"
    )

    # -- Auth / JWT -----------------------------------------------------------
    secret_key_jwt: str = Field(default="", alias="SECRET_KEY_JWT")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=1440, alias="JWT_EXPIRE_MINUTES")  # 24h

    # -- ElevenLabs -----------------------------------------------------------
    elevenlabs_agent_id: Optional[str] = Field(default=None, alias="ELEVENLABS_AGENT_ID")
    elevenlabs_api_key: Optional[str] = Field(default=None, alias="ELEVENLABS_API_KEY")

    # -- Stripe ---------------------------------------------------------------
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_setup_fee_price_id: Optional[str] = Field(
        default=None, alias="STRIPE_SETUP_FEE_PRICE_ID"
    )

    # -- CORS -----------------------------------------------------------------
    cors_origins: List[str] = Field(
        default=["*"], alias="CORS_ORIGINS"
    )

    # -- Rate Limiting --------------------------------------------------------
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")

    # -------------------------------------------------------------------------
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    # -- Validators -----------------------------------------------------------
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached)."""
    return Settings()


# Convenience alias — imported everywhere as `from app.config import settings`
settings = get_settings()
