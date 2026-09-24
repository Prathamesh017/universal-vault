import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import ChunkRow, DocumentRow
from api.schemas import Chunk, RetrievedChunk, RetrievalMode
from api.service.embedding import embed_text

# Higher threshold = stricter. Unrelated text often still scores ~0.4–0.6.
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


def retrieve_chunks(
    db: Session,
    document_id: int,
    question: str,
    mode: RetrievalMode = RetrievalMode.BALANCED,
) -> list[RetrievedChunk]:
    document = db.get(DocumentRow, document_id)
    if document is None:
        return []

    config = RETRIEVAL_CONFIG[mode]
    top_k = config["top_k"]
    threshold = config["threshold"]

    question_embedding = embed_text(question)

    rows = db.scalars(
        select(ChunkRow)
        .where(ChunkRow.document_id == document_id)
        .order_by(ChunkRow.chunk_number)
    ).all()

    scored: list[RetrievedChunk] = []
    for row in rows:
        if not row.embedding:
            continue

        score = cosine_similarity(question_embedding, row.embedding)
        scored.append(
            RetrievedChunk(
                chunk=Chunk.model_validate(row),
                score=round(score, 4),
            )
        )

    if not scored:
        return []

    scored.sort(key=lambda item: item.score, reverse=True)
    best = scored[0].score

    # Nothing is relevant enough
    if best < threshold:
        return []

    # Keep only chunks close to the best match, and above threshold
    filtered = [
        item
        for item in scored
        if item.score >= threshold and (best - item.score) <= 0.12
    ]

    return filtered[:top_k]
