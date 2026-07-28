# GitSense AI Learnings

## Purpose

This document tracks the **current** frontend and backend stack used in GitSense AI, what each piece does in *this* repo today, and interview-style questions for deeper prep.

Progress snapshot: **Week 1 Days 1–4** are largely in place (scaffold, infra, GitHub submit + clone, tree-sitter parsers, parse summary UI). Days 5+ (chunking, embeddings, RAG, agents) are not implemented yet.

---

## Current Frontend Stack

### React + TypeScript

- UI library and language for the SPA.
- Renders Home and Repositories pages, layout, modals, and forms.
- TypeScript types (`Repository`, `RepositoryParseSummary`, `SkippedFile`) keep API payloads explicit.

### Vite

- Dev server and bundler (`npm run dev`).
- Serves the app on port `5173`, with an optional `/api` proxy to the backend.
- Fast HMR for day-to-day UI work.

### Tailwind CSS (v4)

- Utility-first styling via `@tailwindcss/vite`.
- Styles layout, cards, nav, forms, modals, and status badges.
- Custom animation utilities in `index.css` (`animate-fade-up`, `animate-scale-in`, `ui-card`, `skeleton`, etc.).

### React Router (`react-router-dom`)

- Client-side routing.
- Routes today:
  - `/` → Home landing + health status
  - `/repositories` → repository management dashboard
- Shared chrome lives in `AppLayout` with `NavLink` + `Outlet`.
- Page transitions use a fade-only `page-enter` class so `position: fixed` modals are not trapped by transform animations.

### React Query (`@tanstack/react-query`)

- Server-state management for API data.
- Home: health check query.
- Repositories: list query + submit/delete/reindex mutations.
- Parse summary modal: per-repo query keyed by `['parse-summary', repositoryId, 'modal']`.
- Invalidates queries after submit, reindex, and delete.

### Axios (`src/lib/axios.ts` + `src/api/`)

- Shared Axios client with `VITE_API_URL` base URL.
- API modules: `health.ts`, `repositories.ts`.
- `getApiErrorMessage()` surfaces FastAPI `detail` strings to the UI.
- Keeps HTTP details out of page components.

### Lucide React

- Icon set for the repositories dashboard and parse summary modal (`BarChart3`, `X`, `FileCode2`, etc.).

### React Markdown

- Renders markdown on the Home “About” section.
- Prepares the UI for later AI chat / generated docs that return markdown.

### Shadcn UI

- Initialized (New York / slate / Nova preset) as the component foundation.
- Button primitive and utils exist; current pages mostly use native HTML + Tailwind.
- Ready for reusable primitives as the dashboard grows.

### Parse summary modal (`ParseSummaryModal.tsx`)

- Opened from **View parse summary** on each cloned repository card.
- Rendered with `createPortal(..., document.body)` so it centers on the viewport.
- Shows file/symbol/skipped counts, languages, symbol kinds, skip reasons, and a scrollable skipped-file list.
- Close via X, Escape, or backdrop click (with exit animation).

### Socket.io client

- Listed in dependencies and the product spec.
- **Not wired yet** — intended later for streaming chat and live indexing updates.

---

## Current Backend Stack

### FastAPI

- HTTP API framework.
- Mounts routers for root, health, and repositories under `/api/v1`.
- Uses lifespan startup to initialize the database schema.
- CORS allows the Vite frontend origin.

### Uvicorn

- ASGI server that runs FastAPI (`uvicorn main:app --reload` locally / in Docker).
- Serves the API on port `8000`.

### Python 3.12

- Backend runtime (Docker image and project target).
- Foundation for later RAG, agents, and indexing libraries.

### Pydantic Settings (`config.py`)

- Loads config from the project-root `.env`.
- **Required** (no code defaults): `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.
- Also uses `REDIS_URL`, `QDRANT_URL`, and `REPOSITORY_CLONE_DIR`.
- `@computed_field` builds `database_url` and resolves `repository_clone_path`.

### Pydantic schemas

- Request/response models for repositories, parse summary, and symbols (`schemas/repository.py`).
- Validate GitHub URL input and shape API responses.

### psycopg + PostgreSQL

- Relational persistence for repository metadata and parse results.
- Tables: `repositories`, `repository_files`, `repository_symbols`, `repository_skipped_files`.
- On startup: `CREATE TABLE IF NOT EXISTS` for all tables + indexes.
- Service layer manages status lifecycle and parse persistence.

### Repository service + Git

- Validates public GitHub URLs only.
- Deduplicates by URL / full name.
- Runs `git clone --depth 1` synchronously in the request.
- Stores clone path under `REPOSITORY_CLONE_DIR`.
- Status flow: `cloning` → `parsing` → `cloned` / `failed` (also `reindexing` on reindex).
- Supports `DELETE /repositories/{id}` and `POST /repositories/{id}/reindex`.
- Backend Docker image installs `git` so cloning works in containers.

### Tree-sitter parsers (`backend/parsers/`)

- Day 4 language parsing for Go, Python, JavaScript, and TypeScript (`.tsx` uses TSX grammar).
- `extract.py`: tree-sitter queries extract functions, classes/types, methods, imports.
- `service.py`: walks clone directory, persists parsed files/symbols, records skipped files.
- Skips `node_modules`, `.git`, binaries, oversized files, and unsupported extensions.
- Triggered automatically after clone and reindex via `_parse_and_finalize()`.

### Cleanup hooks (`services/cleanup_hooks.py`)

- Stubs for Qdrant/graph cleanup and re-embed on delete/reindex.
- Called today; real vector/graph cleanup comes in later weeks.

### Celery / Redis client / Qdrant client / httpx

- Present in `requirements.txt` / Compose / settings.
- **Not used in app logic yet** — reserved for workers, cache, vectors, and outbound HTTP later.

---

## Supporting Infrastructure

### PostgreSQL

- Stores repository metadata and parse artifacts.
- Local options:
  - Homebrew Postgres with `POSTGRES_HOST=localhost` for `make backend`
  - Docker Compose service `postgres` with `POSTGRES_HOST=postgres` for `make docker-up`
- Desktop UIs (Postico / TablePlus) connect as **localhost:5432** from the Mac.

### Redis

- Compose service only so far.
- Planned for semantic cache and Celery broker/results.

### Qdrant

- Compose service only so far.
- Planned for embeddings / semantic search (Day 5+).

### Docker + Docker Compose

- Services: `frontend`, `backend`, `postgres`, `redis`, `qdrant`.
- Frontend Dockerfile runs `npm install` on start so new deps sync with the anonymous `node_modules` volume.
- Backend Dockerfile includes `git` and tree-sitter dependencies for cloning + parsing.

### Makefile

- Local: `frontend`, `backend`, `start-gitsense-ai`
- Docker: `docker-build`, `docker-up`, `docker-down`, `docker-logs`

### Git ignore for clones

- `**/data/repos/` is gitignored so cloned GitHub repos are not committed as nested repositories.

---

## How The Current Project Uses The Stack

### Frontend flow today

1. Vite starts the React app; `main.tsx` wraps it in `QueryClientProvider`.
2. `App.tsx` defines `BrowserRouter` routes inside `AppLayout`.
3. Home calls `GET /api/v1/health` via React Query.
4. Repositories page lists repos, submits URLs, reindexes, deletes, and opens parse summary modals.
5. Tailwind + custom CSS animations style pages and modals.

### Backend flow today

1. Uvicorn starts FastAPI with a lifespan hook.
2. Lifespan calls `initialize_database()` (Postgres tables ensure).
3. `POST /api/v1/repositories` → parse URL → insert `cloning` → `git clone` → `parsing` → tree-sitter walk → `cloned`/`failed`.
4. `GET /api/v1/repositories` returns rows ordered by `created_at`.
5. `GET /api/v1/repositories/{id}/parse-summary` and `/symbols` return parse results.
6. `POST /reindex` clears parse data, re-clones, re-parses; `DELETE` removes DB rows, parse data, and clone directory.

### Connectivity mental model

```text
Browser  →  React (5173)  →  FastAPI (8000)  →  PostgreSQL (5432)
                                      ↓
                                 git clone → disk (data/repos/...)
                                      ↓
                              tree-sitter parse → repository_* tables
                                      ↓
                                   GitHub HTTPS
```

- Inside Docker: backend uses host name `postgres`.
- On Mac (UI or local backend): use host name `localhost`.

---

## Interview Questions: Frontend

1. Why use React Router instead of keeping everything in one `App.tsx` component?
2. What is the difference between `BrowserRouter`, `Routes`, `Route`, `Outlet`, and `NavLink`?
3. How does React Query’s `useMutation` + `invalidateQueries` keep the repositories list fresh after submit?
4. When would you prefer React Query over local `useState` for API data?
5. Why keep API calls in `src/api/` with a shared Axios client instead of calling HTTP inside every page?
6. What problem does Vite’s proxy solve in local development?
7. Why render the parse summary modal with `createPortal` to `document.body`?
8. Why avoid `transform` animations on a parent wrapper when using `position: fixed` modals?
9. How would you add a third route (for example Chat) without rewriting the layout?
10. What happens in Docker if you add a new npm package but the frontend container keeps an old anonymous `node_modules` volume?
11. How would Socket.io later complement React Query for streaming chat?

## Interview Questions: Backend

1. Why separate route handlers (`repositories.py`) from business logic (`repository_service.py` and `parsers/service.py`)?
2. What does FastAPI’s lifespan do, and why initialize the DB there?
3. How does `APIRouter` prefix stacking produce `/api/v1/repositories/{id}/parse-summary`?
4. Why make `POSTGRES_*` required in Settings instead of hardcoding defaults?
5. Explain `@computed_field` vs a plain `@property` in Pydantic Settings.
6. Why clone with `git clone --depth 1` instead of a full clone for the MVP?
7. Why mark status `cloning` → `parsing` → `cloned`/`failed`?
8. What HTTP status codes fit: invalid URL, duplicate repo, missing git binary, clone failure, parse failure?
9. Why is synchronous clone + parse acceptable for the MVP but risky for large repos later?
10. How would Celery change the submit-repository flow?
11. Why use tree-sitter for Day 4 instead of language-specific AST libraries?
12. What is a “symbol” in GitSense, and what gets stored in `repository_symbols`?
13. Why record skipped files separately instead of only counting them?
14. How does reindex clear stale parse data before re-cloning?

## Interview Questions: Data And Infrastructure

1. Why store repository metadata in PostgreSQL and the code itself on disk?
2. Why should cloned repos under `data/repos/` be gitignored?
3. What is the difference between `POSTGRES_HOST=postgres` and `POSTGRES_HOST=localhost`?
4. Why can Postico fail with “hostname not found” when host is set to `postgres`?
5. What is the difference between a Dockerfile and Docker Compose?
6. Why run Redis and Qdrant in Compose before the app reads from them?
7. What is an anonymous Docker volume, and how did it break `react-router-dom` until rebuilt?
8. Why install `git` in the backend image?
9. How do `repository_files`, `repository_symbols`, and `repository_skipped_files` relate?
10. What data belongs in Postgres vs Qdrant vs Redis in the full GitSense design?

## Interview Prompts You Can Practice Answering

- Explain the current GitSense AI architecture in 2 minutes (through Day 4).
- Walk through what happens when a user submits `https://github.com/owner/repo` end to end.
- Walk through what happens when a user clicks **View parse summary**.
- Why are React Query and FastAPI a strong pair for this MVP?
- Compare local Homebrew Postgres vs Docker Compose Postgres for development.
- How would you move cloning/parsing from request/response to a background worker without breaking the UI?
- Describe how you would add authentication and multi-user repository ownership later.
- Design the next steps: chunking → embeddings → chat retrieval using today’s symbol index.

## What Is Intentionally Not Built Yet

Use this to stay honest in interviews:

- Full file AST dump (symbols only today)
- Chunking, embeddings, Qdrant ingestion
- Hybrid search / BM25
- Chat API and RAG answer generation
- LangGraph agents
- Graph RAG (cleanup hook stub only)
- Semantic caching
- GitHub webhooks / incremental indexing
- JWT auth, Kubernetes, Prometheus / Grafana / LangSmith
