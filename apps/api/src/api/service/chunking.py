



def create_chunks_from_structure(structure: dict) -> list[dict]:
    """Traverse the section tree and return a chunk for each section with content."""
    chunks: list[dict] = []

    def traverse(section: dict, breadcrumb_path: list[str]) -> None:
        current_path = breadcrumb_path + [section.get("title", "")]
        breadcrumb = " > ".join(p for p in current_path if p)

        content = section.get("content", "").strip()
        if content:
            for small_chunk in split_large_text(content):
                chunks.append(
                    {
                        "chunk_number": len(chunks) + 1,
                        "text": small_chunk,
                        "section": current_path[0] if len(current_path) > 0 else None,
                        "subsection": current_path[1] if len(current_path) > 1 else None,
                        "subsubsection": current_path[2]
                        if len(current_path) > 2
                        else None,
                        "breadcrumb": breadcrumb,
                        "heading": section.get("heading"),
                        "level": section.get("level"),
                    }
                )

        for child in section.get("children", []):
            traverse(child, current_path)

    for section in structure.get("sections", []):
        traverse(section, [])

    return chunks


def split_large_text(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 200,
    min_chunk_size: int = 200,
) -> list[str]:
    """
    Split text into smaller chunks if it's too large.

    chunk_size: target size per chunk (2000 chars)
    overlap: overlap between chunks (200 chars) to preserve context
    min_chunk_size: merge a tiny leftover into the previous chunk
    """
    if len(text) <= chunk_size:
        return [text]

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    stride = chunk_size - overlap

    i = 0
    while i < len(text):
        chunk = text[i : i + chunk_size]
        chunks.append(chunk)

        # Last window reached the end
        if i + chunk_size >= len(text):
            break

        i += stride

    # Merge a tiny trailing leftover into the previous chunk
    if len(chunks) > 1 and len(chunks[-1]) < min_chunk_size:
        chunks[-2] = chunks[-2] + chunks[-1][overlap:]
        chunks.pop()

    return chunks
