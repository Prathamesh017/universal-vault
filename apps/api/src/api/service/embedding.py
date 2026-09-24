import os

import requests
from dotenv import load_dotenv

from api.schemas import Chunk

load_dotenv()

EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
# chat/completions → embeddings on the same OpenAI-compatible base


def embed_text(text: str) -> list[float]:
    """Call the embeddings API for a single text string."""
    if not EMBEDDING_API_KEY:
        raise ValueError("API_KEY is missing. Add it to apps/api/.env.")


    response = requests.post(
        EMBEDDING_API_URL,
        headers={
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": EMBEDDING_MODEL_NAME,
            "input": text,
        },
        timeout=60,
    )

    data = response.json()
    if response.status_code != 200 or "error" in data:
        raise RuntimeError(f"Embedding error ({response.status_code}): {data}")

    return data["data"][0]["embedding"]


def handle_embedding(chunks: list[Chunk]) -> list[Chunk]:
    """Embed each chunk; skip ones that already have an embedding."""
    embedded: list[Chunk] = []

    for chunk in chunks:
        if chunk.embedding:
            embedded.append(chunk)
            continue

        try:
            vector = embed_text(chunk.text)
            embedded.append(chunk.model_copy(update={"embedding": vector}))
        except Exception as e:
            print(f"Embedding failed for chunk {chunk.chunk_number}: {e}")
            embedded.append(chunk)

    return embedded
