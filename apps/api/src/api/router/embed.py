from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import ChunkRow, DocumentRow
from api.service.embedding import embed_text

router = APIRouter(prefix="/documents", tags=["embeddings"])


@router.post("/{document_id}/embed")
def embed_document_chunks(document_id: int, db: Session = Depends(get_db)):
    document = db.get(DocumentRow, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    rows = db.scalars(
        select(ChunkRow)
        .where(ChunkRow.document_id == document_id)
        .order_by(ChunkRow.chunk_number)
    ).all()

    embedded = 0
    skipped = 0

    for row in rows:
        if row.embedding:
            skipped += 1
            continue

        row.embedding = embed_text(row.text)
        embedded += 1

    db.commit()

    return {
        "document_id": document_id,
        "total": len(rows),
        "embedded": embedded,
        "skipped": skipped,
    }
