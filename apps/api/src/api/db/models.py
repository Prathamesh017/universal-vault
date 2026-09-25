from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.database import Base


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    chunks: Mapped[list["ChunkRow"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    conversation_history: Mapped[list["ConversationHistoryRow"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class ChunkRow(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str | None] = mapped_column(String, nullable=True)
    subsection: Mapped[str | None] = mapped_column(String, nullable=True)
    subsubsection: Mapped[str | None] = mapped_column(String, nullable=True)
    breadcrumb: Mapped[str] = mapped_column(String, nullable=False)
    heading: Mapped[str | None] = mapped_column(String, nullable=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    document: Mapped["DocumentRow"] = relationship(back_populates="chunks")


class ConversationHistoryRow(Base):
    __tablename__ = "conversation_history"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "question_normalized", name="uq_conversation_history_doc_question"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    question_embedding: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    document: Mapped["DocumentRow"] = relationship(back_populates="conversation_history")


class QueryLogRow(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event: Mapped[str] = mapped_column(String, nullable=False, index=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
