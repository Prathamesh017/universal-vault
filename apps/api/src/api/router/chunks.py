from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import ChunkRow
from api.schemas import Chunk

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.get("")
def get_chunks(
    document_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(ChunkRow).order_by(ChunkRow.id)
    if document_id is not None:
        stmt = stmt.where(ChunkRow.document_id == document_id)

    chunks = [Chunk.model_validate(row) for row in db.scalars(stmt).all()]
    return {"count": len(chunks), "chunks": chunks}
