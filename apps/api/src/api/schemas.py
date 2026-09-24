from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RetrievalMode(str, Enum):
    QUICK = "quick"
    BALANCED = "balanced"
    DETAILED = "detailed"


class Document(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    title: str
    total_chunks: int = 0
    uploaded_at: datetime


class Chunk(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
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


class QueryRequest(BaseModel):
    question: str
    mode: RetrievalMode = RetrievalMode.BALANCED


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float
