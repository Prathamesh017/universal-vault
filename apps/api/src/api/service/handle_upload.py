from datetime import UTC, datetime
from itertools import count

from api.models.model import Chunk, Document
from api.service.chunking import create_chunks_from_structure
from api.service.parser import parse_document

_document_ids = count(1)


def process_upload(filename: str, text: str) -> dict:

    structure = parse_document(text)
    document = Document(
        id=next(_document_ids),
        filename=filename,
        title=structure.get("title") or filename,
        total_chunks=0,
        uploaded_at=datetime.now(UTC),
    )

    raw_chunks = create_chunks_from_structure(structure)
    chunks = [
        Chunk(
            **raw_chunk,
            document_id=document.id,
            embedding=[],
        )
        for raw_chunk in raw_chunks
    ]

    document.total_chunks = len(chunks)

    return {
        "document": document,
        "chunks": chunks,
        "structure": structure,
    }
