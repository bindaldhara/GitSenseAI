# GitSense AI — Future Enhancements

This file tracks improvements that are **not built yet**, prioritized from a scan of the current codebase against `docs/final_doc.md` and `docs/QnA.md`.

Last updated: 2026-07-28 (after Day 3: sync public clone + repositories dashboard)

## Already Built (do not re-list as future)

- React + Vite + Tailwind frontend with React Router (`/`, `/repositories`)
- React Query health check and repository submit/list UI
- FastAPI health + `POST/GET /api/v1/repositories`
- Repository lifecycle: `DELETE /api/v1/repositories/{id}` and `POST /api/v1/repositories/{id}/reindex`
- Cascade cleanup/re-embed stubs in `backend/services/cleanup_hooks.py` (Qdrant/graph not wired yet)
- PostgreSQL `repositories` table and status lifecycle (`cloning` / `reindexing` → `cloned` / `failed`)
- Synchronous `git clone --depth 1` for **public** GitHub URLs
- Docker Compose (frontend, backend, postgres, redis, qdrant) and Makefile targets

---

## Priority 0 — Next Clone Improvements

### 1. Queue cloning for background processing

**Why:** Today `create_repository_submission` and reindex still block the HTTP request on `git clone`. Large repos risk timeouts and tie up API workers.

**Direction:**

- Insert a repository row with status `queued` (or `cloning`)
- Enqueue a Celery task (Redis already in Compose; `celery` already in `requirements.txt`)
- Return quickly from `POST /api/v1/repositories` (for example `202 Accepted`)
- Worker updates status to `cloned` / `failed`
- Frontend polls list (or later Socket.io) so the dashboard reflects async progress

**Touch points:** `backend/services/repository_service.py`, new `backend/workers/`, Redis broker settings, Repositories page status UX

### 2. Clone private repositories as well

**Why:** Day 3 explicitly supports public GitHub URLs only. Real teams need private repos.

**Direction:**

- Accept a GitHub PAT or GitHub App installation token (never commit secrets)
- Authenticated clone URL or `GIT_ASKPASS` / credential helper
- Store credential reference securely (env / secrets manager), not in the `repositories.url` column
- Extend validation beyond “public only” while keeping host checks
- Document local vs Docker secret injection

**Touch points:** `repository_service.py`, `config.py` / `.env`, schemas, Repositories UI (optional token field or server-side token)

### 3. Async-aware dashboard status

**Why:** UI currently waits on synchronous submit/reindex responses. Background cloning needs clear `queued` / `cloning` / `cloned` / `failed` feedback with polling or websockets.

---

## Priority 1 — Week 1 Days 4–7 (MVP RAG)

| Enhancement | Why / notes |
|---|---|
| Language parsers (Go, Python, JS, TS) | Day 4; no parsers yet; read from `clone_path` |
| Chunking + embeddings + Qdrant ingestion | Day 5; Qdrant runs in Compose but `vector_store/` is unused |
| Chat API (retrieval + generation) | Day 6; `rag/` stub only |
| Chat UI + markdown answers | Day 7; no `/chat` route; markdown is Home-only today |
| Wire Redis for real use | Container + dep exist; unused until Celery / cache |

---

## Priority 2 — Week 2 (Production AI)

| Enhancement | Why / notes |
|---|---|
| Hybrid search (BM25 + vectors) | Day 8 |
| Semantic caching + analytics | Day 9; `cache/` stub |
| LangGraph agents (Router, Code, Docs, Arch) | Days 10–11; `agents/` empty |
| Graph RAG + dependency mapping | Day 12; `graph_rag/` stub; no graph DB in Compose yet |
| Mermaid / architecture diagrams | Day 13 |
| JWT auth + chat history + multi-repo | Day 14 |
| Repo ownership / RBAC | Repos are global rows with no user linkage |

---

## Priority 3 — Week 3 (Differentiators)

| Enhancement | Why / notes |
|---|---|
| MCP tools (`clone_repo`, `search_file`, `generate_docs`, …) | Days 15–16; `tools/` stub |
| GitHub webhooks (push / PR / merge) | Day 17 |
| Incremental indexing | Day 18; depends on webhooks + embeddings |
| AI observability (tokens, latency, cost) | Day 19 |
| Kubernetes + GitHub Actions CI/CD | Day 20; Compose-only today |
| Nginx / production edge | Listed in tech stack; not present |
| Polish (demo, architecture diagram, resume bullets) | Day 21 |

---

## Priority 4 — Longer-Term Product Ideas

From `docs/final_doc.md` future enhancements:

- VS Code extension
- Slack integration
- GitHub App (also helps private repos + webhooks)
- Voice interface
- AI pull request reviewer
- Automated unit test generation
- Security vulnerability detection

---

## Smaller Technical Follow-Ups

- Optional full/deeper clone policy (today is `--depth 1` only)
- Streaming chat responses (FastAPI streaming and/or Socket.io)
- Language / directory filters for search once retrieval exists
- Ollama / local embedding option
- Explicit graph store choice for Graph RAG (not only Qdrant + Postgres)
- Frontend Docker `node_modules` volume drift when adding npm packages (partially mitigated by startup `npm install`)

---

## Suggested Near-Term Order

1. Background clone queue (Celery + Redis)
2. Private repo cloning (token-based auth)
3. Async status UX (polling / websockets) for queued clones
4. Parsers → chunking → embeddings → chat API/UI
