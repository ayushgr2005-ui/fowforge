# FowForge Architecture

## Request path

### Ingestion
1. Browser uploads TXT/MD/PDF.
2. FastAPI validates extension and size.
3. PDF text is extracted with pypdf; text/Markdown is UTF-8 decoded.
4. Text is chunked with overlap.
5. Sentence Transformer creates normalized vectors.
6. PostgreSQL stores the document and pgvector stores chunk embeddings.

### Query
1. Browser sends a question.
2. FastAPI validates the request and applies rate limiting.
3. The query is embedded with the same embedding model.
4. pgvector performs cosine-distance ordering.
5. Top chunks become source contexts (`S1`, `S2`, ...).
6. The grounded prompt instructs the LLM to use only those contexts.
7. The answer is normalized to a consistent citation syntax.
8. The API persists user/assistant messages and source traces.
9. Streaming uses SSE for progressive UI rendering.

## Reliability controls

- Input schema validation
- File extension and size limits
- Centralized HTTP/validation/internal errors
- Request IDs
- Structured request logs
- Rate limiting in Redis
- Optional API-key auth
- Health/readiness endpoints
- Prometheus request/latency metrics
- Docker healthchecks
- CI tests/builds

## Evaluation controls

The evaluation harness intentionally measures more than retrieval:

- retrieval source hit
- citation presence
- lexical groundedness regression signal
- unknown-answer handling

These are lightweight engineering regression checks. A production research benchmark should use a larger labelled dataset and stronger semantic/LLM-judge metrics.
