-- Query flow event logs for metrics
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
