from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import ConversationHistoryRow
from api.service.embedding import embed_text
from api.service.retrieve import cosine_similarity

SEMANTIC_THRESHOLD = 0.90


def normalize_question(question: str) -> str:
    return " ".join(question.strip().lower().split())


def lookup_exact(db: Session, document_id: int, question: str) -> ConversationHistoryRow | None:
    normalized = normalize_question(question)
    return db.scalars(
        select(ConversationHistoryRow).where(
            ConversationHistoryRow.document_id == document_id,
            ConversationHistoryRow.question_normalized == normalized,
        )
    ).first()


def lookup_semantic(
    db: Session, document_id: int, question: str
) -> ConversationHistoryRow | None:
    rows = db.scalars(
        select(ConversationHistoryRow).where(ConversationHistoryRow.document_id == document_id)
    ).all()
    if not rows:
        return None

    try:
        question_embedding = embed_text(question)
    except Exception as e:
        print(f"Cache semantic embed failed: {e}")
        return None

    best_row = None
    best_score = 0.0
    for row in rows:
        if not row.question_embedding:
            continue
        score = cosine_similarity(question_embedding, row.question_embedding)
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is None or best_score < SEMANTIC_THRESHOLD:
        return None
    return best_row


def lookup_cache(db: Session, document_id: int, question: str) -> dict | None:
    """Exact match first, then semantic. Returns {answer, question} or None."""
    exact = lookup_exact(db, document_id, question)
    if exact is not None:
        return {"answer": exact.answer, "question": exact.question}

    semantic = lookup_semantic(db, document_id, question)
    if semantic is not None:
        return {"answer": semantic.answer, "question": semantic.question}

    return None


def save_cache(db: Session, document_id: int, question: str, answer: str) -> None:
    """Upsert a successful Q&A for this document."""
    normalized = normalize_question(question)
    if not normalized or not answer:
        return

    try:
        embedding = embed_text(question)
    except Exception as e:
        print(f"Cache save embed failed: {e}")
        embedding = []

    existing = db.scalars(
        select(ConversationHistoryRow).where(
            ConversationHistoryRow.document_id == document_id,
            ConversationHistoryRow.question_normalized == normalized,
        )
    ).first()

    if existing is not None:
        existing.question = question
        existing.answer = answer
        existing.question_embedding = embedding
    else:
        db.add(
            ConversationHistoryRow(
                document_id=document_id,
                question=question,
                question_normalized=normalized,
                question_embedding=embedding,
                answer=answer,
                created_at=datetime.now(timezone.utc),
            )
        )

    db.commit()
