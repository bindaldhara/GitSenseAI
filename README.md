# GitSense AI

Agentic Software Intelligence Platform for indexing GitHub repositories, parsing source code, and preparing data for RAG workflows.

---

## Prerequisites

Install these before running the project locally:

| Tool | Version | Why |
|---|---|---|
| **Node.js** | `^20.19.0` or `>=22.12.0` | Frontend (Vite + React) |
| **npm** | Comes with Node | Frontend dependencies |
| **Python** | `3.12` | Backend (FastAPI) |
| **pip** | Latest | Backend dependencies |
| **Git** | Latest | Repository cloning |
| **PostgreSQL** | `16` | Repository + parse metadata |
| **Make** | Latest | Convenience commands |
| **Docker** + **Docker Compose** | Latest (optional) | Run full stack in containers |
| **nvm** (recommended) | Latest | `make frontend` uses Node 22.12.0 |

Optional (provisioned in Docker Compose, not required for Day 4 core flow):

- **Redis** — planned for Celery / caching
- **Qdrant** — planned for embeddings (Day 5+)

---

## Tech Stack

### Frontend
- React + TypeScript
- Vite
- Tailwind CSS
- React Router
- React Query
- Axios
- React Markdown
- Lucide React
- Shadcn UI (initialized)

### Backend
- FastAPI
- Python 3.12
- Uvicorn
- Pydantic Settings
- psycopg (PostgreSQL)
- tree-sitter (Go, Python, JavaScript, TypeScript parsers)

### Data & Infrastructure
- PostgreSQL — repositories, parsed files, symbols, skipped files
- Redis — reserved for workers/cache
- Qdrant — reserved for vector search
- Docker Compose — multi-service local stack

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd gitsense-ai
```

### 2. Create environment file

```bash
cp .env.example .env
```

Edit `.env` with your local values (see sample below).

### 3. Start PostgreSQL

**Option A — Homebrew (local backend)**

```bash
brew install postgresql@16
brew services start postgresql@16
createdb gitsense
```

Set in `.env`:

```env
POSTGRES_HOST=localhost
```

**Option B — Docker Compose**

Postgres starts automatically with `make docker-up`. Set in `.env`:

```env
POSTGRES_HOST=postgres
```

### 4. Install backend dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 5. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 6. Create clone directory (if needed)

Ensure the path in `REPOSITORY_CLONE_DIR` exists. Example:

```bash
mkdir -p backend/data/repos
```

---

## Environment sample

Create `.env` in the project root:

```env
# App
APP_NAME=GitSense AI
APP_VERSION=0.1.0
API_V1_PREFIX=/api/v1
FRONTEND_ORIGIN=http://localhost:5173

# PostgreSQL (required — no code defaults)
POSTGRES_DB=gitsense
POSTGRES_USER=gitsense
POSTGRES_PASSWORD=gitsense
POSTGRES_PORT=5432

# Use localhost for local backend (Homebrew / published Docker port)
POSTGRES_HOST=localhost

# Use postgres when backend runs inside Docker Compose
# POSTGRES_HOST=postgres

# Supporting services
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Local path where git clones are stored
REPOSITORY_CLONE_DIR=backend/data/repos
```

**Docker Compose note:** when the backend container runs, use `POSTGRES_HOST=postgres`. When you run `make backend` on your Mac, use `POSTGRES_HOST=localhost`.

**Frontend API URL (Docker frontend):** set in `docker-compose.yml` as `VITE_API_URL=http://localhost:8000`.

---

## How to start the server

### Option 1 — Start both services (recommended for local dev)

From the project root:

```bash
make start-gitsense-ai
```

This runs backend and frontend together with streaming logs.

### Option 2 — Start services separately

**Backend**

```bash
make backend
```

API: [http://localhost:8000](http://localhost:8000)  
Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

**Frontend**

```bash
make frontend
```

App: [http://localhost:5173](http://localhost:5173)

### Option 3 — Docker Compose (full stack)

```bash
make docker-up
```

Services:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Qdrant | http://localhost:6333 |

Stop containers:

```bash
make docker-down
```

View logs:

```bash
make docker-logs
```

---

## Quick verification

**Health check**

```bash
curl http://localhost:8000/api/v1/health
```

**Submit a public GitHub repo**

```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -d '{"url":"https://github.com/octocat/Hello-World"}'
```

**List repositories**

```bash
curl http://localhost:8000/api/v1/repositories
```

**Parse summary (after status is `cloned`)**

```bash
curl "http://localhost:8000/api/v1/repositories/1/parse-summary?skipped_limit=20"
```

---

## Project structure

```text
gitsense-ai/
├── backend/          # FastAPI API, parsers, services
├── frontend/         # React UI
├── docker/           # Dockerfiles
├── docs/             # Project docs (final_doc, learnings, QnA)
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Useful Makefile commands

| Command | Description |
|---|---|
| `make backend` | Run FastAPI locally |
| `make frontend` | Run Vite dev server |
| `make start-gitsense-ai` | Run backend + frontend |
| `make docker-build` | Build Docker images |
| `make docker-up` | Start full Docker stack |
| `make docker-down` | Stop Docker stack |
| `make docker-logs` | Follow container logs |

---

