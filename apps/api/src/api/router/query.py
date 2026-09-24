from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import DocumentRow
from api.schemas import QueryRequest
from api.service.retrieve import RETRIEVAL_CONFIG, retrieve_chunks

router = APIRouter(tags=["query"])


@router.post("/query/{document_id}")
def query_document(
    document_id: int,
    body: QueryRequest,
    db: Session = Depends(get_db),
):
    document = db.get(DocumentRow, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    config = RETRIEVAL_CONFIG[body.mode]
    results = retrieve_chunks(db, document_id, body.question, body.mode)

    return {
        "document_id": document_id,
        "question": body.question,
        "mode": body.mode,
        "top_k": config["top_k"],
        "threshold": config["threshold"],
        "count": len(results),
        "chunks": results,
    }
