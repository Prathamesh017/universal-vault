from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import ChunkRow, DocumentRow
from api.schemas import Chunk, Document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def get_documents(db: Session = Depends(get_db)):
    rows = db.scalars(select(DocumentRow).order_by(DocumentRow.id)).all()
    documents = [Document.model_validate(row) for row in rows]
    return {"count": len(documents), "documents": documents}


@router.get("/{document_id}/chunks")
def get_chunks_by_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(DocumentRow, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    rows = db.scalars(
        select(ChunkRow)
        .where(ChunkRow.document_id == document_id)
        .order_by(ChunkRow.chunk_number)
    ).all()
    chunks = [Chunk.model_validate(row) for row in rows]

    return {
        "document_id": document_id,
        "count": len(chunks),
        "chunks": chunks,
    }
