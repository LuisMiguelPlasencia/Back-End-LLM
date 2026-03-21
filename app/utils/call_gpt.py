# ---------------------------------------------------------------------------
# Thin wrapper around OpenAI's responses API
# ---------------------------------------------------------------------------

from __future__ import annotations

from openai import OpenAI

from app.config import settings


def call_gpt(
    client: OpenAI,
    prompt: str,
    model: str = "",
    ensure_json: bool = True,
) -> str:
    """Send *prompt* to the OpenAI responses endpoint and return the text.

    Parameters
    ----------
    client:
        An authenticated ``OpenAI`` instance.
    prompt:
        The full prompt string.
    model:
        Model name override; defaults to ``settings.openai_default_model``.
    ensure_json:
        When ``True`` the response is constrained to valid JSON output.
    """
    model = model or settings.openai_default_model

    kwargs: dict = {"model": model, "input": prompt}
    if ensure_json:
        kwargs["text"] = {"format": {"type": "json_object"}}

    response = client.responses.create(**kwargs)
    return response.output_text
