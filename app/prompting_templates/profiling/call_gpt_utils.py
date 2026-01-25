"""Compatibility wrapper for older profiling modules.

New code should use:
- `app.utils.openai_client.get_openai_client()` to create the client
- `app.utils.call_gpt.call_gpt(client, prompt, model=...)` to execute requests
"""

from openai import OpenAI

from app.utils.call_gpt import call_gpt as _call_gpt


def call_gpt(client: OpenAI, prompt: str, model: str = "gpt-4.1-nano-2025-04-14") -> str:
    return _call_gpt(client, prompt, model=model)
