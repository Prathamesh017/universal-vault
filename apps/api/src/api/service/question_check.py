import json
import os

import requests
from dotenv import load_dotenv

from api.constant import question_check_prompt

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("TEXT_MODEL_NAME")
API_URL = os.getenv("API_URL")


def check_question(question: str, description: str) -> dict:
    """LLM gate before retrieval. Returns {isValid, reason}."""
    if not description.strip():
        return {
            "isValid": True,
            "reason": "No document description was provided, so the question check was skipped.",
        }

    if not API_KEY or not API_URL:
        return {
            "isValid": True,
            "reason": "Question check is unavailable right now, so retrieval will continue.",
        }

    prompt = question_check_prompt.format(
        description=description,
        question=question,
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
            timeout=60,
        )
        data = response.json()
        if response.status_code != 200 or "error" in data:
            raise RuntimeError(str(data))

        raw = data["choices"][0]["message"]["content"]
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)

        is_valid = bool(parsed.get("isValid", False))
        reason = str(parsed.get("reason", "")).strip()
        if not reason:
            reason = (
                "Your question looks valid for this document."
                if is_valid
                else "Your question could not be used for this document."
            )

        return {"isValid": is_valid, "reason": reason}
    except Exception as e:
        print(f"Question check failed: {e}")
        return {
            "isValid": True,
            "reason": "Question check failed temporarily, so retrieval will continue.",
        }
