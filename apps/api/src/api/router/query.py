from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import DocumentRow
from api.schemas import QueryRequest
from api.service.question_check import check_question
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

    check = check_question(body.question, document.description or "")
    if not check["isValid"]:
        return {
            "isValid": False,
            "message": check["reason"],
            "chunks": [],
        }

    config = RETRIEVAL_CONFIG[body.mode]
    result = retrieve_chunks(db, document_id, body.question, body.mode)
    chunks = result["chunks"]

    return {
        "isValid": True,
        "message": check["reason"],
        "document_id": document_id,
        "question": body.question,
        "query_used": result["query_used"],
        "rewritten": result["rewritten"],
        "mode": body.mode,
        "top_k": config["top_k"],
        "threshold": config["threshold"],
        "count": len(chunks),
        "chunks": chunks,
    }
