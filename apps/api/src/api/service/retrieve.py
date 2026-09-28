import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.constant import query_rewrite_prompt
from api.db.models import ChunkRow, DocumentRow
from api.schemas import Chunk, RetrievedChunk, RetrievalMode
from api.service.answer import MODEL_NAME, call_main_model
from api.service.embedding import embed_text
from api.service import logging_service as logs
from api.service import ollama as ollama_llm

NEAR_BAND = 0.12

RETRIEVAL_CONFIG = {
    RetrievalMode.QUICK: {"top_k": 3, "threshold": 0.78},
    RetrievalMode.BALANCED: {"top_k": 5, "threshold": 0.68},
    RetrievalMode.DETAILED: {"top_k": 10, "threshold": 0.58},
}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def score_chunks(db: Session, document_id: int, question: str) -> list[RetrievedChunk]:
    question_embedding = embed_text(question)
    rows = db.scalars(
        select(ChunkRow).where(ChunkRow.document_id == document_id)
    ).all()

    scored = [
        RetrievedChunk(
            chunk=Chunk.model_validate(row),
            score=round(cosine_similarity(question_embedding, row.embedding), 4),
        )
        for row in rows
        if row.embedding
    ]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored


def pick_chunks(
    scored: list[RetrievedChunk], top_k: int, min_score: float = 0.0
) -> list[RetrievedChunk]:
    """Keep top_k items within NEAR_BAND of the best, optionally above min_score."""
    if not scored or scored[0].score < min_score:
        return []
    best = scored[0].score
    return [
        item
        for item in scored
        if item.score >= min_score and best - item.score <= NEAR_BAND
    ][:top_k]


def rewrite_query(question: str, nearest: list[RetrievedChunk]) -> str:
    if not nearest:
        return question

    prompt = query_rewrite_prompt.format(
        question=question,
        chunks="\n\n".join(
            f"- ({item.score}) {item.chunk.breadcrumb}: {item.chunk.text[:400]}"
            for item in nearest
        ),
    )

    try:
        text = call_main_model(prompt, timeout=60).strip().strip('"')
        return text or question
    except Exception as e:
        print(f"Rewrite LLM failed ({MODEL_NAME}), trying Ollama: {e}")
        try:
            text = ollama_llm.generate_text(prompt, timeout=60).strip().strip('"')
            return text or question
        except Exception as ollama_error:
            print(f"Ollama rewrite failed: {ollama_error}")
            return question


def build_result(
    chunks: list[RetrievedChunk], question: str, rewritten: bool
) -> dict:
    return {"chunks": chunks, "rewritten": rewritten, "query_used": question}


def retrieve_chunks(
    db: Session,
    document_id: int,
    question: str,
    mode: RetrievalMode = RetrievalMode.BALANCED,
    allow_rewrite: bool = True,
) -> dict:
    if db.get(DocumentRow, document_id) is None:
        logs.log_event(
            db,
            logs.RETRIEVAL_NO_RESULTS,
            document_id=document_id,
            question=question,
            detail={"reason": "document_missing"},
        )
        return build_result([], question, False)

    top_k = RETRIEVAL_CONFIG[mode]["top_k"]
    threshold = RETRIEVAL_CONFIG[mode]["threshold"]

    scored = score_chunks(db, document_id, question)
    strong = pick_chunks(scored, top_k, min_score=threshold)
    if strong:
        logs.log_event(
            db,
            logs.RETRIEVAL_SUCCESS,
            document_id=document_id,
            question=question,
            detail={"chunk_count": len(strong), "top_score": strong[0].score},
        )
        return build_result(strong, question, False)

    if not scored or not allow_rewrite:
        logs.log_event(
            db,
            logs.RETRIEVAL_NO_RESULTS,
            document_id=document_id,
            question=question,
            detail={"reason": "no_strong_chunks"},
        )
        return build_result([], question, False)

    logs.log_event(
        db,
        logs.RETRIEVAL_REWRITE_NEEDED,
        document_id=document_id,
        question=question,
        detail={
            "top_score": scored[0].score if scored else None,
            "threshold": threshold,
        },
    )

    rewritten = rewrite_query(question, pick_chunks(scored, top_k))
    retry = pick_chunks(
        score_chunks(db, document_id, rewritten), top_k, min_score=threshold
    )

    if retry:
        logs.log_event(
            db,
            logs.RETRIEVAL_REWRITE_SUCCESS,
            document_id=document_id,
            question=question,
            detail={
                "query_used": rewritten,
                "chunk_count": len(retry),
                "top_score": retry[0].score,
            },
        )
    else:
        logs.log_event(
            db,
            logs.RETRIEVAL_NO_RESULTS,
            document_id=document_id,
            question=question,
            detail={"reason": "rewrite_failed", "query_used": rewritten},
        )

    return build_result(retry, rewritten, True)
