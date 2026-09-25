-- Per-document Q&A cache for exact + semantic question reuse
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
