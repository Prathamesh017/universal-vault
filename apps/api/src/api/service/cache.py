from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import ConversationHistoryRow
from api.service.embedding import embed_text
from api.service import logging_service as logs
from api.service.retrieve import cosine_similarity

SEMANTIC_THRESHOLD = 0.90
# Log near_miss when below threshold but still close
NEAR_MISS_FLOOR = 0.85


def normalize_question(question: str) -> str:
    return " ".join(question.strip().lower().split())


def lookup_exact(
    db: Session, document_id: int, question: str
) -> ConversationHistoryRow | None:
    normalized = normalize_question(question)
    return db.scalars(
        select(ConversationHistoryRow).where(
            ConversationHistoryRow.document_id == document_id,
            ConversationHistoryRow.question_normalized == normalized,
        )
    ).first()


def lookup_semantic(
    db: Session, document_id: int, question: str
) -> tuple[ConversationHistoryRow | None, float]:
    """Returns (row_or_none, best_score)."""
    rows = db.scalars(
        select(ConversationHistoryRow).where(
            ConversationHistoryRow.document_id == document_id
        )
    ).all()
    if not rows:
        return None, 0.0

    try:
        question_embedding = embed_text(question)
    except Exception as e:
        print(f"Cache semantic embed failed: {e}")
        return None, 0.0

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
        return None, best_score
    return best_row, best_score


def lookup_cache(db: Session, document_id: int, question: str) -> dict | None:
    """Exact match first, then semantic. Logs cache metrics."""
    exact = lookup_exact(db, document_id, question)
    if exact is not None:
        logs.log_event(
            db,
            logs.CACHE_EXACT_HIT,
            document_id=document_id,
            question=question,
        )
        return {"answer": exact.answer, "question": exact.question}

    semantic, score = lookup_semantic(db, document_id, question)
    if semantic is not None:
        logs.log_event(
            db,
            logs.CACHE_SEMANTIC_HIT,
            document_id=document_id,
            question=question,
            detail={"score": round(score, 4), "matched_question": semantic.question},
        )
        return {"answer": semantic.answer, "question": semantic.question}

    if NEAR_MISS_FLOOR <= score < SEMANTIC_THRESHOLD:
        logs.log_event(
            db,
            logs.CACHE_NEAR_MISS,
            document_id=document_id,
            question=question,
            detail={"score": round(score, 4), "threshold": SEMANTIC_THRESHOLD},
        )
    else:
        logs.log_event(
            db,
            logs.CACHE_MISS,
            document_id=document_id,
            question=question,
            detail={"score": round(score, 4)} if score else {},
        )

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
        existing.created_at = datetime.now(timezone.utc)
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
