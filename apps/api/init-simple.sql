CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
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

CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    question_normalized TEXT NOT NULL,
    question_embedding JSONB NOT NULL DEFAULT '[]'::jsonb,
    answer TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, question_normalized)
);

CREATE INDEX IF NOT EXISTS idx_conversation_history_document_id ON conversation_history(document_id);

CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    event TEXT NOT NULL,
    question TEXT,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_logs_document_id ON query_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_event ON query_logs(event);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
