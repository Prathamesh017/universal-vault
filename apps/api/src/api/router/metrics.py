from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.service.logging_service import get_metrics, get_recent_logs

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics(
    document_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_metrics(db, document_id)


@router.get("/metrics/logs")
def metrics_logs(
    document_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return {"logs": get_recent_logs(db, document_id, limit)}
