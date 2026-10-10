# FowForge — Production-Style Grounded AI Knowledge Platform

FowForge is an end-to-end RAG product reference implementation designed around the engineering patterns expected in a modern product-company AI backend: ingestion, embeddings, pgvector retrieval, grounded generation, citations, streaming, rate limiting, persistence, observability, evaluation, testing, Docker and CI.

## Product capabilities

- Upload TXT / Markdown / PDF knowledge documents
- Deterministic chunking with overlap
- Local embedding generation with Sentence Transformers
- PostgreSQL + pgvector vector persistence
- Cosine-similarity retrieval with scores
- Grounded LLM answers through an OpenAI-compatible provider
- Citation normalization (`[S1]` and `【S1】` → `[S1]`)
- Explicit unknown-answer behavior to reduce hallucination
- Server-Sent Events streaming
- Conversation + retrieval trace persistence
- Redis-backed IP rate limiting
- Optional API-key authentication for protected API routes
- Request IDs and structured request logging
- Prometheus request counters and latency histograms
- Health and readiness endpoints
- Input validation, file type/size limits, security headers and centralized errors
- Evaluation harness for retrieval, citations, groundedness and unknown handling
- Lightweight concurrent load-test harness
- Backend unit tests + GitHub Actions CI
- Docker Compose for repeatable local deployment
- Responsive React/Vite product UI

## Architecture

```text
                         +----------------------+
                         |      React/Vite      |
                         | upload + chat + SSE  |
                         +----------+-----------+
                                    |
                              HTTP / SSE
                                    |
                         +----------v-----------+
                         |      FastAPI API      |
                         | validation / auth     |
                         | request IDs / errors  |
                         +----+-------------+----+
                              |             |
                     ingestion|             |chat
                              |             |
                 +------------v--+       +--v----------------+
                 | chunk -> embed |       | retrieval -> LLM  |
                 +-------+-------+       +---------+----------+
                         |                         |
                 +-------v-------------------------v-------+
                 | PostgreSQL + pgvector   Redis           |
                 | docs / chunks / traces  rate limiting   |
                 +-----------------------------------------+
                              |
                     +--------v---------+
                     | Eval + Prometheus |
                     | tests + metrics   |
                     +-------------------+
```

## Quick start — Windows

1. Copy `.env.example` to `.env`.
2. Set `LLM_API_KEY` locally. Never commit or paste the key into GitHub/chat.
3. Start everything:

```cmd
docker compose up -d --build
```

4. Open `http://localhost:5173`.
5. API docs: `http://localhost:8000/docs`
6. Health: `http://localhost:8000/api/health`
7. Readiness: `http://localhost:8000/api/ready`
8. Metrics: `http://localhost:8000/metrics`

You can also run `START_FOWFORGE.cmd`.

## Verification

After the stack is running:

```cmd
VERIFY_FOWFORGE.cmd
```

The verification script checks containers, API health, backend tests and the evaluation harness.

For a small local performance smoke test:

```cmd
python evals\load_test.py
```

Do not present load-test numbers as production capacity. They are environment-specific measurements.

## Evaluation

`evals/dataset.jsonl` includes answerable and unanswerable cases. The evaluator reports:

- Retrieval Accuracy
- Citation Accuracy
- Groundedness Score
- Unknown Handling

The current small dataset is a regression suite, not a universal quality guarantee. Expand it with representative domain documents before reporting benchmark numbers.

## Production configuration

For a deployed environment, set:

```env
ENVIRONMENT=production
AUTH_ENABLED=true
API_KEY=<long-random-secret>
CORS_ORIGINS=https://your-frontend.example
```

Keep secrets outside source control. Put TLS termination, a managed PostgreSQL instance, managed Redis, secret management, container image scanning and horizontal scaling at the deployment layer.

## Reverse-engineering order

1. `backend/app/api/routes.py` — API contracts, validation and request flow.
2. `backend/app/services/rag.py` — end-to-end RAG orchestration.
3. `backend/app/services/retrieval.py` — vector retrieval.
4. `backend/app/services/ingestion.py` — parsing, chunking and embeddings.
5. `backend/app/services/llm.py` — grounded prompting, citations and streaming.
6. `backend/app/main.py` — middleware, health, metrics and lifecycle.
7. `frontend/src/main.jsx` — product UX and SSE client.
8. `evals/` — how quality is measured.

## Resume positioning

> Built FowForge, an end-to-end production-style RAG platform with React/Vite, FastAPI, PostgreSQL/pgvector, Redis rate limiting, grounded LLM generation, source citations, SSE streaming, conversation traces, Prometheus observability, automated evaluation, tests, Docker and CI.

Only claim measured performance numbers after running the included load/evaluation harness on the actual deployment.
