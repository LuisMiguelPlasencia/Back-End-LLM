# ---------------------------------------------------------------------------
# Singleton OpenAI client
# ---------------------------------------------------------------------------
# Avoids re-instantiation on every request.  Import the ready-made instance:
#
#     from app.utils.openai_client import openai_client
# ---------------------------------------------------------------------------

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from app.config import settings


@lru_cache(maxsize=1)
def get_openai_client(api_key: str | None = None) -> OpenAI:
    """Return (and cache) an OpenAI client.

    Uses the explicitly provided *api_key* or falls back to ``settings.openai_api_key``.
    """
    resolved_key = api_key or settings.openai_api_key
    if not resolved_key:
        raise ValueError(
            "Missing OpenAI API key. Set OPENAI_API_KEY in your .env file."
        )
    return OpenAI(api_key=resolved_key)


# Pre-built convenience instance — import this where you need it.
openai_client: OpenAI = get_openai_client()
