-- Add description to documents for upload + pre-query relevance checks
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT '';
