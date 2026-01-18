import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, "../../src")
load_dotenv()
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
from openai import OpenAI

client = OpenAI(api_key=OPENAI_TOKEN)


def call_gpt(prompt: str) -> str:
    response = client.responses.create(
        model="gpt-4.1-nano-2025-04-14",
        input=prompt,
    )
    return response.output_text
