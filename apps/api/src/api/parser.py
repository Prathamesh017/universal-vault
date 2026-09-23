# backend/src/parser.py

import json
import os

import requests
from dotenv import load_dotenv
from api.constant import parser_prompt
load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
API_URL = os.getenv("API_URL")


def parse_document(text: str) -> dict:
    """Parse with error handling"""
    if not API_KEY:
        raise ValueError("API_KEY is missing. Add it to apps/api/.env.")

    try:
        final_prompt = parser_prompt + text

        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": final_prompt,
                    }
                ],
            },
            timeout=300,
        )

        data = response.json()

        if response.status_code != 200 or "error" in data:
            raise RuntimeError(f"LLM error ({response.status_code}): {data}")

        json_str = data["choices"][0]["message"]["content"]
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        structure = json.loads(json_str)
        return structure

    except (json.JSONDecodeError, requests.Timeout, requests.RequestException) as e:
        print(f"Parse failed ({type(e).__name__}: {e}), falling back to regex parse...")
        return fallback_parse(text)



# backend/src/chunker.py






def fallback_parse(text: str) -> dict:
    """Simple regex-based parsing if LLM fails"""
    sections = []
    lines = text.split("\n")

    current_section = None
    for line in lines:
        # Count # to determine level
        level = len(line) - len(line.lstrip("#"))
        if level > 0 and level <= 5:
            title = line.lstrip("#").strip()
            section = {
                "level": level,
                "title": title,
                "heading": line,
                "content": "",
                "children": [],
            }
            sections.append(section)
            current_section = section
        elif current_section and line.strip():
            current_section["content"] += line + "\n"

    return {"title": "Document", "sections": sections}
