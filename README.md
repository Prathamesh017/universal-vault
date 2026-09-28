# Universal Vault

A RAG (Retrieval-Augmented Generation) API: upload a Markdown document, and ask questions about it. Answers are generated only from the document's content.

The API is built with FastAPI, stores documents, chunks, embeddings, cache, and logs in Postgres, and works with any OpenAI-compatible LLM. A local Ollama model answers simple questions and acts as a fallback when the main model fails.

## Features

- Markdown upload with heading-aware chunking and embeddings
- Retrieval with cosine similarity, per-question-type thresholds, and one-shot query rewrite
- Question validity check (rejects off-topic or keyword-only questions)
- Rule-based question classification (definition / how-to / comparison / troubleshooting / factual) that picks the retrieval mode
- Model routing: simple questions → Ollama first; everything else → main model with Ollama fallback
- Q&A cache (exact + semantic match)
- Follow-up handling ("tell me more") using the last 5 Q&As
- Query event logging with a `/metrics` endpoint
- Per-IP rate limiting (60 requests/minute, 1000/day) on the query endpoint

## Repository layout

```
apps/
  api/                 FastAPI backend (Python, uv)
    migrations/        SQL migration files
    init-simple.sql    Full schema, run automatically on first Postgres start
    docker-compose.yaml
    src/api/
      router/          HTTP endpoints
      service/         Retrieval, answer, cache, history, logging, rate limit
      db/              SQLAlchemy models, connection, migration runner
  web/                 Next.js scaffold (frontend not built yet)
packages/              Shared TS configs and UI package (Turborepo)
sample-example.md      Sample document for testing
```

## Prerequisites

| Tool | Version | Used for |
|------|---------|----------|
| [Docker](https://www.docker.com/) | any recent | Runs Postgres |
| [uv](https://docs.astral.sh/uv/) | latest | Python env + dependencies for the API |
| Python | 3.13+ | Installed automatically by uv if missing |
| [Node.js](https://nodejs.org/) | 24+ | Monorepo scripts / web app |
| [pnpm](https://pnpm.io/) | 11+ | Package manager for the monorepo |
| [Ollama](https://ollama.com/) | latest | Local model for simple questions and fallback |

You also need an API key for an OpenAI-compatible provider that offers both a chat model and an embedding model.

## Installation

### 1. Clone and install dependencies

```sh
git clone <repo-url> universal-vault
cd universal-vault
pnpm install

cd apps/api
uv sync
```

`uv sync` creates `apps/api/.venv` and installs the Python dependencies from `uv.lock`.

### 2. Start Postgres (Docker)

Postgres runs in Docker using the `pgvector/pgvector:pg15` image (standard Postgres 15 with the pgvector extension available).

```sh
cd apps/api
pnpm db:up          # same as: docker compose up -d
```

This starts a container named `rag_postgres`:

| Setting | Value |
|---------|-------|
| Host port | `5433` (mapped to 5432 inside the container) |
| Database | `rag_db` |
| User / password | `postgres` / `postgres` |

Port **5433** is used so it doesn't clash with a local Postgres on 5432.

On the **first** start (when the Docker volume is empty), Postgres automatically runs `init-simple.sql`, which creates every table. Check it's healthy with:

```sh
docker ps          # STATUS should show "healthy"
```

To stop it: `pnpm db:down`. Data is kept in the `postgres_data` volume. To wipe everything and start fresh, run `docker compose down -v`.

### 3. Configure environment variables

Create `apps/api/.env`:

```env
# Main chat model (any OpenAI-compatible chat/completions endpoint)
API_KEY=your-api-key
API_URL=https://your-provider.example.com/v1/chat/completions
TEXT_MODEL_NAME=your-chat-model

# Embedding model (OpenAI-compatible embeddings endpoint)
EMBEDDING_API_KEY=your-api-key
EMBEDDING_API_URL=https://your-provider.example.com/v1/embeddings
EMBEDDING_MODEL_NAME=your-embedding-model

# Postgres (matches docker-compose.yaml)
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/rag_db

# Local Ollama
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=tinyllama
```

| Variable | Purpose |
|----------|---------|
| `API_KEY`, `API_URL`, `TEXT_MODEL_NAME` | Main LLM: document parsing, question check, query rewrite, follow-up resolution, answers |
| `EMBEDDING_API_KEY`, `EMBEDDING_API_URL`, `EMBEDDING_MODEL_NAME` | Embeddings for chunks and cached questions |
| `DATABASE_URL` | Postgres connection (defaults to the Docker setup above if omitted) |
| `OLLAMA_URL`, `OLLAMA_MODEL` | Local model for simple questions and fallback |

> **Keep the embedding model fixed.** All stored embeddings must come from the same model. If you switch embedding models, clear existing embeddings (chunks and cache) and re-embed, otherwise similarity scores will fail due to mismatched vector sizes.

### 4. Run migrations

```sh
cd apps/api
pnpm db:migrate     # same as: uv run python -m api.db.migrate
```

See [Migrations](#migrations) below for what this does. It's safe to run any time.

### 5. Set up Ollama

```sh
ollama pull tinyllama     # or whichever model you set in OLLAMA_MODEL
ollama serve              # skip if the Ollama app is already running
```

The API still works without Ollama; simple questions and fallbacks will just go to the main model.

### 6. Start the API

```sh
cd apps/api
pnpm dev            # uv run uvicorn api.main:app --reload --port 8000
```

Or from the repo root: `pnpm dev:api`.

- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs

On startup the API also calls SQLAlchemy `create_all`, which creates any missing tables from the models.

### 7. Try it

From the repo root:

```sh
# Upload a document
curl -X POST http://localhost:8000/upload \
  -F "file=@sample-example.md" \
  -F "description=CloudSync product manual: installation, configuration, usage, troubleshooting"

# Embed any chunks that are missing embeddings (upload already embeds)
curl -X POST http://localhost:8000/documents/1/embed

# Ask a question
curl -X POST http://localhost:8000/query/1 \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CloudSync?"}'
```

The `description` is used by the question check to reject off-topic questions, so give each document a short, accurate one.

## Migrations

There are two layers of schema setup:

1. **`init-simple.sql`**: the full, current schema. Postgres runs it automatically only when the Docker volume is created for the first time. Fresh setups get every table from this file.
2. **`migrations/*.sql`**: incremental changes for databases created *before* a table or column existed. They bring older databases up to date without wiping data.

`pnpm db:migrate` runs `src/api/db/migrate.py`, which:

1. Creates a `schema_migrations` table if it doesn't exist
2. Reads all `migrations/*.sql` files in filename order
3. Skips files already recorded in `schema_migrations`
4. Runs each new file and records its filename

All migration files use `IF NOT EXISTS`, so running them on a fresh database (where `init-simple.sql` already created everything) is harmless; they're simply recorded as applied.

| File | What it does |
|------|--------------|
| `001_add_document_description.sql` | Adds `description` to `documents` (used by the question check) |
| `002_add_qa_cache.sql` | Creates `conversation_history`: cached Q&A per document (normalized question, question embedding, answer). Used by the cache and by follow-up handling |
| `003_add_query_logs.sql` | Creates `query_logs`: one row per pipeline event (cache hit/miss, retrieval, rejections, history), used by `/metrics` |

**Adding a new migration:** create the next numbered file (e.g. `004_add_something.sql`), use `IF NOT EXISTS` where possible, also add the change to `init-simple.sql` so fresh setups match, and update the SQLAlchemy model in `src/api/db/models.py`. Then run `pnpm db:migrate`.

### Tables

| Table | Contents |
|-------|----------|
| `documents` | Uploaded documents: filename, title, description, chunk count |
| `chunks` | Chunk text, heading breadcrumb, and embedding (stored as JSONB) |
| `conversation_history` | Q&A cache and recent history per document |
| `query_logs` | Pipeline events for metrics |
| `schema_migrations` | Which migration files have been applied |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Upload a Markdown file (`file`) with an optional `description`; parses, chunks, and embeds it |
| `GET` | `/documents` | List documents |
| `GET` | `/documents/{id}/chunks` | List a document's chunks |
| `POST` | `/documents/{id}/embed` | Embed chunks that don't have embeddings yet |
| `GET` | `/chunks` | List chunks |
| `POST` | `/query/{document_id}` | Ask a question: body `{"question": "..."}` (rate limited) |
| `GET` | `/metrics` | Event counts (cache, retrieval, pipeline); optional `?document_id=` |
| `GET` | `/metrics/logs` | Recent pipeline events; optional `?document_id=` |

### Query response

```json
{
  "isValid": true,
  "found": true,
  "message": "CloudSync is a cloud-based file synchronization platform...",
  "cached": false,
  "document_id": 1,
  "question": "What is CloudSync?",
  "query_used": "What is CloudSync?",
  "rewritten": false,
  "question_type": "definition",
  "mode": "quick"
}
```

| Field | Meaning |
|-------|---------|
| `isValid` | `false` only when the question check rejected the question (off-topic or keywords only) |
| `found` | `true` when an answer was produced (from cache, history, or the document) |
| `message` | Answer, "no match" message, clarifying question, or rejection reason |
| `cached` | Answer came from the Q&A cache |
| `query_used` | The question actually searched (after follow-up resolution or query rewrite) |
| `rewritten` | `query_used` differs from what the user typed |
| `question_type`, `mode` | Rule-based classification and the retrieval mode it selected |

## Query flow

1. **Prepare question**: detect follow-ups ("tell me more"); using the last 5 Q&As, either answer from history, ask the user to clarify, or rewrite into a standalone question
2. **Classify**: keyword rules pick a question type → retrieval mode (quick / balanced / detailed)
3. **Cache lookup**: exact normalized match, then semantic match (≥ 0.90 similarity)
4. **Question check**: LLM verifies the question fits the document and is a real question
5. **Retrieve**: embed the question, score chunks by cosine similarity, keep top chunks above the mode's threshold; if none, rewrite the query once and retry
6. **Answer**: simple questions → Ollama then main model; others → main model then Ollama; the answer must be supported by the chunks
7. **Save + log**: found answers are cached; every step logs an event for `/metrics`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `connection refused` on port 5433 | Postgres isn't running: `cd apps/api && pnpm db:up` |
| `relation "..." does not exist` | Run `pnpm db:migrate`, or recreate the volume with `docker compose down -v && pnpm db:up` |
| Similarity errors / shape mismatch | Embedding model changed; clear embeddings and cache, then re-embed |
| Simple questions are slow | Ollama isn't running or its model isn't pulled, so it falls back to the main model |
| `429 Rate limit exceeded` | More than 60 queries/minute or 1000/day from your IP; wait, or restart the API to reset (limits are in memory) |
| `uv sync` fails with permission errors | Run it outside restricted shells/sandboxes |

## Useful scripts

From the repo root:

| Command | What it does |
|---------|--------------|
| `pnpm dev:api` | Start the API |
| `pnpm dev:web` | Start the Next.js scaffold on port 3000 |
| `pnpm format:api` | Format Python code with ruff |

From `apps/api`:

| Command | What it does |
|---------|--------------|
| `pnpm db:up` / `pnpm db:down` | Start / stop Postgres |
| `pnpm db:migrate` | Apply pending migrations |
| `pnpm dev` | Start the API with reload |
| `pnpm lint` / `pnpm lint:fix` | Lint with ruff |



## Limitations

This is a learning/portfolio project focused on understanding how a RAG system works end to end, so some production concerns are intentionally out of scope.

- **No frontend yet.** The main goal was the RAG pipeline itself; the API is used through Swagger (`/docs`) or `curl`.
- **Markdown only.** Chunking relies on Markdown headings. Other formats (PDF, DOCX, HTML) could be supported by converting them to Markdown before upload.
- **pgvector isn't used as expected yet.** Embeddings are stored as JSONB in Postgres and scored with cosine similarity in Python. This is fine for a few documents, but pgvector with an index would move the search into Postgres and scale much better.
- **Embedding search only.** There's no keyword (full-text/BM25) search alongside it, so exact terms like error codes or version numbers can be missed.
- **One document per query.** Questions can't span multiple documents.
- **Shared history per document.** Follow-ups use the last 5 Q&As for the document, not per user or session, so everyone querying the same document shares that context.

