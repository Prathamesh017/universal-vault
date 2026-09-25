import json
import os
import re

import requests
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.constant import resolve_followup_prompt
from api.db.models import ConversationHistoryRow
from api.service import logging_service as logs

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("TEXT_MODEL_NAME")
API_URL = os.getenv("API_URL")

HISTORY_LIMIT = 5
DEFAULT_CLARIFICATION = "What topic were you referring to?"

FOLLOWUP_PATTERNS = [
    r"\btell me more\b",
    r"\bcontinue\b",
    r"\belaborate\b",
    r"\bdetails\b",
    r"\bexpand on\b",
    r"\bmore about\b",
    r"\bwhat about\b",
    r"\band then\b",
    r"\bsame\b",
]


def is_followup(question: str) -> bool:
    text = question.strip().lower()
    if not text:
        return False
    return any(re.search(pattern, text) for pattern in FOLLOWUP_PATTERNS)


def topic_from_turns(turns: list) -> str:
    for row in reversed(turns):
        if not is_followup(row.question):
            return row.question
    return turns[-1].question


def fallback_search_question(turns: list) -> str:
    topic = topic_from_turns(turns)
    return f"What else should I know about: {topic}"


def weak_search_question(question: str) -> bool:
    text = question.strip().lower()
    if not text or is_followup(text):
        return True
    if "(about:" in text:
        return True
    return len(text.split()) < 4


def prepare_question(db: Session, document_id: int, question: str) -> dict:
    """
    Follow-up handling using last 5 conversation_history rows.
    Returns {needs_history, action, question, message}
      action: "none" | "answer" | "search" | "clarify"
    """
    if not is_followup(question):
        return {
            "needs_history": False,
            "action": "none",
            "question": question,
            "message": "",
        }

    rows = db.scalars(
        select(ConversationHistoryRow)
        .where(ConversationHistoryRow.document_id == document_id)
        .order_by(ConversationHistoryRow.created_at.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    turns = list(reversed(list(rows)))

    if not turns:
        logs.log_event(
            db,
            logs.HISTORY_CLARIFY,
            document_id=document_id,
            question=question,
            detail={"turns": 0},
        )
        return {
            "needs_history": True,
            "action": "clarify",
            "question": question,
            "message": DEFAULT_CLARIFICATION,
        }

    history = "\n".join(
        f"{i}. Q: {row.question}\n   A: {row.answer}"
        for i, row in enumerate(turns, start=1)
    )

    action = "search"
    message = ""
    search_question = fallback_search_question(turns)

    if API_KEY and API_URL:
        try:
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
                            "content": resolve_followup_prompt.format(
                                history=history, question=question
                            ),
                        }
                    ],
                },
                timeout=60,
            )
            data = response.json()
            if response.status_code != 200 or "error" in data:
                raise RuntimeError(data)

            raw = data["choices"][0]["message"]["content"]
            raw = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)

            action = str(parsed.get("action", "search")).strip().lower()
            message = str(parsed.get("message", "")).strip()
            llm_question = str(parsed.get("question", "")).strip()

            if action not in {"answer", "search", "clarify"}:
                action = "search"

            if action == "search":
                search_question = (
                    llm_question
                    if llm_question and not weak_search_question(llm_question)
                    else fallback_search_question(turns)
                )
        except Exception as e:
            print(f"Resolve follow-up failed: {e}")
            action = "search"
            search_question = fallback_search_question(turns)

    if action == "answer" and message:
        logs.log_event(
            db,
            logs.HISTORY_ANSWERED,
            document_id=document_id,
            question=question,
            detail={"turns": len(turns)},
        )
        return {
            "needs_history": True,
            "action": "answer",
            "question": question,
            "message": message,
        }

    if action == "clarify" or (action == "answer" and not message):
        logs.log_event(
            db,
            logs.HISTORY_CLARIFY,
            document_id=document_id,
            question=question,
            detail={"turns": len(turns)},
        )
        return {
            "needs_history": True,
            "action": "clarify",
            "question": question,
            "message": message or DEFAULT_CLARIFICATION,
        }

    logs.log_event(
        db,
        logs.HISTORY_RESOLVED,
        document_id=document_id,
        question=question,
        detail={"resolved_question": search_question, "turns": len(turns)},
    )
    return {
        "needs_history": True,
        "action": "search",
        "question": search_question,
        "message": "",
    }
