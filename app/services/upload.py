import json
import os
import re
from openai import OpenAI
from fastapi import UploadFile, File
import shutil
from pypdf import PdfReader


from app.utils.call_gpt import call_gpt
from app.utils.openai_client import get_openai_client

DEFAULT_MODEL = "gpt-4.1-nano-2025-04-14"

os.makedirs("uploads", exist_ok=True)

def clean_text(text: str) -> str:
    # Remove multiple newlines
    text = re.sub(r"\n{2,}", "\n", text)

    # Remove extra spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Trim
    return text.strip()

def chunk_text(text: str, max_chars: int = 1000):
    chunks = []
    current = ""

    for paragraph in text.split("\n"):
        if len(current) + len(paragraph) <= max_chars:
            current += paragraph + "\n"
        else:
            chunks.append(current.strip())
            current = paragraph + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks

def read_pdf(file: UploadFile = File(...)) -> dict:
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    reader = PdfReader(file_path)
    raw_text = ""

    for page in reader.pages:
        raw_text += page.extract_text() or ""

    cleaned_text = clean_text(raw_text)
    chunks = chunk_text(cleaned_text)

    return {
        "filename": file.filename,
        "total_chars": len(cleaned_text),
        "chunks_count": len(chunks),
        "chunks": chunks,  # preview only
    }

def llamar_gpt_hasta_que_este_bien(client: OpenAI, prompt: str, model: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = json.loads(call_gpt(client, prompt, model=model))
            return response
        except Exception as e: 
            if attempt < max_retries - 1:
                print(f"llamando a gpt otra vez porque no daba un JSON bien formado... (intento {attempt + 1}/{max_retries})")
            else:
                print(f"Error después de {max_retries} intentos: {e}")
                raise

def summarize_chunk(chunk: str) -> dict:
    client = get_openai_client()

    prompt = f"""
        You are an assistant that creates study summaries.

        Summarize the following text in a way that is:
        - Clear and easy to understand
        - Suitable for a student
        - Focused on key concepts

        Rules:
        - Create a short descriptive title
        - Write 3 to 5 bullet points
        - Do NOT copy text verbatim
        - Do NOT add information that is not present
        - Keep language simple

        Return the result ONLY in valid JSON with this format:
        {{
        "title": "...",
        "summary": ["...", "..."]
        }}

        Text:
        \"\"\"
        {chunk}
        \"\"\"
        """

    response = llamar_gpt_hasta_que_este_bien(client, prompt, model=DEFAULT_MODEL)

    print(response)

    try:
        return response
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON returned by model: {response}")

def summarize_chunks(chunks: list[str]) -> list[dict]:
    summaries = []

    for chunk in chunks:
        summary = summarize_chunk(chunk)
        summaries.append(summary)

    return summaries

