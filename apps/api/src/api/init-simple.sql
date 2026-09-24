CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT NOT NULL,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    section TEXT,
    subsection TEXT,
    subsubsection TEXT,
    breadcrumb TEXT NOT NULL,
    heading TEXT,
    level INTEGER,
    embedding JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
