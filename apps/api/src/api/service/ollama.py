"""Local Ollama text helper — answers simple questions and is the fallback for the main LLM."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")


def generate_text(prompt: str, timeout: int = 120) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    data = response.json()
    if response.status_code != 200 or "error" in data:
        raise RuntimeError(f"Ollama error ({response.status_code}): {data}")
    return str(data.get("response", "")).strip()
