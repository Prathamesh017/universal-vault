from datetime import UTC, datetime

from api.db.database import SessionLocal
from api.db.models import ChunkRow, DocumentRow
from api.schemas import Chunk, Document
from api.service.chunking import create_chunks_from_structure
from api.service.embedding import handle_embedding
from api.service.parser import parse_document


def process_upload(filename: str, text: str) -> dict:
    structure = parse_document(text)

    with SessionLocal() as db:
        doc_row = DocumentRow(
            filename=filename,
            title=structure.get("title") or filename,
            total_chunks=0,
            uploaded_at=datetime.now(UTC),
        )
        db.add(doc_row)
        db.flush()

        raw_chunks = create_chunks_from_structure(structure)
        chunks = [
            Chunk(**raw_chunk, document_id=doc_row.id, embedding=[])
            for raw_chunk in raw_chunks
        ]

        print("Started embedding process", len(chunks), "chunks")
        chunks = handle_embedding(chunks)

        for chunk in chunks:
            db.add(
                ChunkRow(
                    document_id=chunk.document_id,
                    chunk_number=chunk.chunk_number,
                    text=chunk.text,
                    section=chunk.section,
                    subsection=chunk.subsection,
                    subsubsection=chunk.subsubsection,
                    breadcrumb=chunk.breadcrumb,
                    heading=chunk.heading,
                    level=chunk.level,
                    embedding=chunk.embedding,
                )
            )

        doc_row.total_chunks = len(chunks)
        db.commit()
        db.refresh(doc_row)

        saved_chunks = [
            Chunk.model_validate(row)
            for row in doc_row.chunks
        ]

        return {
            "document": Document.model_validate(doc_row),
            "chunks": saved_chunks,
            "structure": structure,
        }
