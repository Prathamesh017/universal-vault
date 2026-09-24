import json
import os

import requests
from dotenv import load_dotenv

from api.constant import answer_from_chunks_prompt
from api.schemas import RetrievedChunk

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("TEXT_MODEL_NAME")
API_URL = os.getenv("API_URL")

NO_MATCH = "No matching information was found for your question."


def format_chunks_for_llm(chunks: list[RetrievedChunk]) -> str:
    parts = [
        f"- score={item.score} | {item.chunk.breadcrumb}\n{item.chunk.text}"
        for item in chunks
    ]
    return "\n\n".join(parts)


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> dict:
    """LLM-only: given chunks, return {found, message}."""
    if not chunks:
        return {"found": False, "message": NO_MATCH}

    if not API_KEY or not API_URL:
        return {"found": False, "message": "Answer generation is unavailable right now."}

    prompt = answer_from_chunks_prompt.format(
        question=question,
        chunks=format_chunks_for_llm(chunks),
    )

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=90,
        )
        data = response.json()
        if response.status_code != 200 or "error" in data:
            raise RuntimeError(data)

        raw = data["choices"][0]["message"]["content"]
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)

        found = bool(parsed.get("satisfied", False))
        message = str(parsed.get("message", "")).strip()
        if not message:
            message = (
                "Here is what I found based on the document." if found else NO_MATCH
            )

        return {"found": found, "message": message if found else NO_MATCH}
    except Exception as e:
        print(f"Answer generation failed: {e}")
        return {"found": False, "message": NO_MATCH}
