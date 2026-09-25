from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.db.models import QueryLogRow

# Event names — keep stable; metrics maps these into nested buckets
CACHE_EXACT_HIT = "cache.exact_hit"
CACHE_SEMANTIC_HIT = "cache.semantic_hit"
CACHE_MISS = "cache.miss"
CACHE_NEAR_MISS = "cache.near_miss"

RETRIEVAL_SUCCESS = "retrieval.success"
RETRIEVAL_REWRITE_NEEDED = "retrieval.rewrite_needed"
RETRIEVAL_REWRITE_SUCCESS = "retrieval.rewrite_success"
RETRIEVAL_NO_RESULTS = "retrieval.no_results"

QUESTION_REJECTED = "pipeline.question_rejected"
ANSWER_FOUND = "pipeline.answer_found"
ANSWER_NOT_FOUND = "pipeline.answer_not_found"
HISTORY_RESOLVED = "history.resolved"
HISTORY_CLARIFY = "history.clarify"
HISTORY_ANSWERED = "history.answered"



def log_event(
    db: Session,
    event: str,
    document_id: int | None = None,
    question: str | None = None,
    detail: dict | None = None,
) -> None:
    """Append one query-flow event. Failures never break the main request."""
    try:
        db.add(
            QueryLogRow(
                document_id=document_id,
                event=event,
                question=question,
                detail=detail or {},
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"log_event failed ({event}): {e}")


def count_event(counts: dict, event: str) -> int:
    return int(counts.get(event, 0))


def get_metrics(db: Session, document_id: int | None = None) -> dict:
    stmt = select(QueryLogRow.event, func.count(QueryLogRow.id)).group_by(
        QueryLogRow.event
    )
    if document_id is not None:
        stmt = stmt.where(QueryLogRow.document_id == document_id)

    counts = {event: count for event, count in db.execute(stmt).all()}

    return {
        "document_id": document_id,
        "cache": {
            "exact_hits": count_event(counts, CACHE_EXACT_HIT),
            "semantic_hits": count_event(counts, CACHE_SEMANTIC_HIT),
            "misses": count_event(counts, CACHE_MISS),
            "near_misses": count_event(counts, CACHE_NEAR_MISS),
        },
        "retrieval": {
            "success": count_event(counts, RETRIEVAL_SUCCESS),
            "rewrite_needed": count_event(counts, RETRIEVAL_REWRITE_NEEDED),
            "rewrite_success": count_event(counts, RETRIEVAL_REWRITE_SUCCESS),
            "no_results": count_event(counts, RETRIEVAL_NO_RESULTS),
        },
        "pipeline": {
            "question_rejected": count_event(counts, QUESTION_REJECTED),
            "answer_found": count_event(counts, ANSWER_FOUND),
            "answer_not_found": count_event(counts, ANSWER_NOT_FOUND),
            "history_resolved": count_event(counts, HISTORY_RESOLVED),
            "history_clarify": count_event(counts, HISTORY_CLARIFY),
            "history_answered": count_event(counts, HISTORY_ANSWERED),
        },
    }


def get_recent_logs(
    db: Session,
    document_id: int | None = None,
    limit: int = 50,
) -> list[dict]:
    stmt = select(QueryLogRow).order_by(QueryLogRow.created_at.desc()).limit(limit)
    if document_id is not None:
        stmt = stmt.where(QueryLogRow.document_id == document_id)

    return [
        {
            "id": row.id,
            "document_id": row.document_id,
            "event": row.event,
            "question": row.question,
            "detail": row.detail,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in db.scalars(stmt).all()
    ]
