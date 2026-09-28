from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import DocumentRow
from api.schemas import QueryRequest, QuestionType, RetrievalMode
from api.service.answer import generate_answer
from api.service.cache import lookup_cache, save_cache
from api.service.history import prepare_question
from api.service import logging_service as logs
from api.service.question_check import check_question
from api.service.retrieve import (
    QUESTION_TYPE_MODE,
    classify_question_rule_based,
    retrieve_chunks,
)

router = APIRouter(tags=["query"])


def query_response(
    *,
    is_valid: bool,
    found: bool,
    message: str,
    document_id: int | None = None,
    question: str | None = None,
    query_used: str | None = None,
    rewritten: bool = False,
    question_type: QuestionType | None = None,
    mode: RetrievalMode | None = None,
    cached: bool = False,
) -> dict:
    payload = {
        "isValid": is_valid,
        "found": found,
        "message": message,
        "cached": cached,
    }
    if document_id is not None:
        payload.update(
            {
                "document_id": document_id,
                "question": question,
                "query_used": query_used,
                "rewritten": rewritten,
                "question_type": question_type,
                "mode": mode,
            }
        )
    return payload


@router.post("/query/{document_id}")
def query_document(
    document_id: int,
    body: QueryRequest,
    db: Session = Depends(get_db),
):
    document = db.get(DocumentRow, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    prepared = prepare_question(db, document_id, body.question)
    if prepared["action"] in ("answer", "clarify"):
        return query_response(
            is_valid=True,
            found=prepared["action"] == "answer",
            message=prepared["message"],
            document_id=document_id,
            question=body.question,
            query_used=body.question,
            rewritten=False,
            cached=False,
        )
    question = prepared["question"]
    question_type = classify_question_rule_based(question)
    mode = QUESTION_TYPE_MODE[question_type]

    cached = lookup_cache(db, document_id, question)
    if cached is not None:
        return query_response(
            is_valid=True,
            found=True,
            message=cached["answer"],
            document_id=document_id,
            question=body.question,
            query_used=question,
            rewritten=question != body.question,
            question_type=question_type,
        mode=mode,
            cached=True,
        )

    check = check_question(question, document.description or "")
    if not check["isValid"]:
        logs.log_event(
            db,
            logs.QUESTION_REJECTED,
            document_id=document_id,
            question=body.question,
            detail={"reason": check["reason"]},
        )
        return query_response(
            is_valid=False, found=False, message=check["reason"]
        )

    retrieval = retrieve_chunks(db, document_id, question, mode)
    result = generate_answer(question, retrieval["chunks"])

    if result["found"]:
        save_cache(db, document_id, question, result["message"])
        logs.log_event(
            db,
            logs.ANSWER_FOUND,
            document_id=document_id,
            question=body.question,
            detail={"rewritten": retrieval["rewritten"]},
        )
    else:
        logs.log_event(
            db,
            logs.ANSWER_NOT_FOUND,
            document_id=document_id,
            question=body.question,
            detail={"rewritten": retrieval["rewritten"]},
        )

    return query_response(
        is_valid=True,
        found=result["found"],
        message=result["message"],
        document_id=document_id,
        question=body.question,
        query_used=retrieval["query_used"],
        rewritten=retrieval["rewritten"],
        question_type=question_type,
        mode=mode,
        cached=False,
    )
