from datetime import datetime

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: int
    filename: str
    title: str
    total_chunks: int = 0
    uploaded_at: datetime


class Chunk(BaseModel):
    chunk_number: int
    text: str
    section: str | None = None
    subsection: str | None = None
    subsubsection: str | None = None
    breadcrumb: str
    heading: str | None = None
    level: int | None = None
    embedding: list[float] = Field(default_factory=list)
    document_id: int = Field(..., description="References Document.id")
