import json
import os
import re

import requests
from dotenv import load_dotenv

from api.constant import answer_from_chunks_prompt
from api.schemas import RetrievedChunk
from api.service import ollama as ollama_llm

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("TEXT_MODEL_NAME")
API_URL = os.getenv("API_URL")

NO_MATCH = "No matching information was found for your question."

COMPLEX_KEYWORDS = [
    "integrate", "troubleshoot", "compare",
    "architecture", "design", "multiple",
]

SIMPLE_KEYWORDS = [
    "what is", "define", "explain", "version",
]


def has_keyword(text: str, keywords: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords)


def is_simple_question(question: str) -> bool:
    """Complex keywords win; unknown questions go to the main model."""
    text = question.lower()
    if has_keyword(text, COMPLEX_KEYWORDS):
        return False
    return has_keyword(text, SIMPLE_KEYWORDS)


def call_main_model(prompt: str, timeout: int = 90) -> str:
    if not API_KEY or not API_URL:
        raise RuntimeError("Main text LLM is not configured")

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
        timeout=timeout,
    )
    data = response.json()
    if response.status_code != 200 or "error" in data:
        raise RuntimeError(data)
    return data["choices"][0]["message"]["content"]


def format_chunks_for_llm(chunks: list[RetrievedChunk]) -> str:
    parts = [
        f"- score={item.score} | {item.chunk.breadcrumb}\n{item.chunk.text}"
        for item in chunks
    ]
    return "\n\n".join(parts)


def parse_answer(raw: str) -> dict:
    raw = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)
    found = bool(parsed.get("satisfied", False))
    if not found:
        return {"found": False, "message": NO_MATCH}
    message = str(parsed.get("message", "")).strip()
    return {
        "found": True,
        "message": message or "Here is what I found based on the document.",
    }


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> dict:
    """LLM-only: given chunks, return {found, message}."""
    if not chunks:
        return {"found": False, "message": NO_MATCH}

    prompt = answer_from_chunks_prompt.format(
        question=question,
        chunks=format_chunks_for_llm(chunks),
    )

    main = (MODEL_NAME, call_main_model)
    ollama = (ollama_llm.OLLAMA_MODEL, ollama_llm.generate_text)
    order = [ollama, main] if is_simple_question(question) else [main, ollama]

    for name, call in order:
        try:
            return parse_answer(call(prompt, timeout=90))
        except Exception as e:
            print(f"Answer LLM failed ({name}): {e}")
    return {"found": False, "message": NO_MATCH}
