import os

from dotenv import load_dotenv
from openai import OpenAI


def get_openai_client(api_key: str | None = None) -> OpenAI:
    """Create an OpenAI client.

    Prefers the explicitly provided `api_key`, otherwise loads `.env` and reads
    `OPENAI_API_KEY`.
    """

    load_dotenv(override=True)  # loads .env into environment if present

    resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not resolved_key:
        raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in your environment/.env")

    return OpenAI(api_key=resolved_key)
