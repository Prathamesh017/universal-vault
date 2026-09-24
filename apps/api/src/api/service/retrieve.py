import os

import numpy as np
import requests
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.constant import query_rewrite_prompt
from api.db.models import ChunkRow, DocumentRow
from api.schemas import Chunk, RetrievedChunk, RetrievalMode
from api.service.embedding import embed_text

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("TEXT_MODEL_NAME")
API_URL = os.getenv("API_URL")
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
    if not API_KEY or not API_URL or not nearest:
        return question

    chunks_text = "\n\n".join(
        f"- ({item.score}) {item.chunk.breadcrumb}: {item.chunk.text[:400]}"
        for item in nearest
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
                "messages": [
                    {
                        "role": "user",
                        "content": query_rewrite_prompt.format(
                            question=question, chunks=chunks_text
                        ),
                    }
                ],
            },
            timeout=60,
        )
        data = response.json()
        if response.status_code != 200 or "error" in data:
            raise RuntimeError(data)
        text = data["choices"][0]["message"]["content"].strip().strip('"')
        return text or question
    except Exception as e:
        print(f"Query rewrite failed: {e}")
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
) -> dict:
    if db.get(DocumentRow, document_id) is None:
        return build_result([], question, False)

    top_k = RETRIEVAL_CONFIG[mode]["top_k"]
    threshold = RETRIEVAL_CONFIG[mode]["threshold"]

    scored = score_chunks(db, document_id, question)
    strong = pick_chunks(scored, top_k, min_score=threshold)
    if strong:
        return build_result(strong, question, False)

    if not scored:
        return build_result([], question, False)

    rewritten = rewrite_query(question, pick_chunks(scored, top_k))
    retry = pick_chunks(
        score_chunks(db, document_id, rewritten), top_k, min_score=threshold
    )
    return build_result(retry, rewritten, True)
