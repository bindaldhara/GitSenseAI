# GitSense AI QnA

This file records clarified decisions so future work does not rely on assumptions.

## Confirmed Decisions

### 2026-07-28

- Skill scope: use a project skill in `.cursor/skills/` inside this repository.
- Clarifications location: keep questions and confirmed answers in `docs/QnA.md`.
- Product and architecture reference: use `docs/final_doc.md`.
- Teaching mode: explain commands in detail, including why they are used and what they do.
- Frontend package manager: use `npm`.
- Backend dependency management: use `requirements.txt` with `pip`.
- UI setup: initialize Shadcn UI during Day 1.
- Shadcn style: use `new-york`.
- Shadcn base color: use `slate`.
- Shadcn current CLI path: use the current preset-based CLI flow.
- Shadcn preset: use `Nova`.
- Shadcn project name: use `gitsense-ai-frontend`.
- Git setup: run `git init` only for now, without creating the first commit.
- Git default branch: use `main`.
- Frontend runtime strategy: keep the current frontend versions and use a supported Node version instead of downgrading the toolchain.
- Makefile target names: use `frontend`, `backend`, and `start-gitsense-ai`.
- Combined Makefile start behavior: run both services in the foreground with streaming logs.
- Makefile Docker mode: keep the existing local-run targets and add separate Docker Compose targets.
- Learnings doc location: use `docs/learnings.md`.
- Learnings interview depth: use a deeper interview-prep section.
- Active documentation structure: use `docs/final_doc.md` and `docs/QnA.md`.
- Day 3 persistence: persist submitted repositories in PostgreSQL now.
- Day 3 clone execution: clone repositories synchronously inside the API request.
- Day 3 clone location: use a configurable local clone path under the backend workspace.
- Day 3 frontend scope: keep the current single-page app and add the repository submission flow there.
- Frontend routing: introduce React Router with a Home landing page and a separate `/repositories` dashboard for repository management.
- Day 3 GitHub scope: support public GitHub repository URLs only for now.
- Local Postgres strategy: use native Homebrew PostgreSQL (no Docker for the database in local development).
- Postgres config strictness: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` are required from `.env` with no code fallback defaults.
- Interview answers location: use `docs/answers.txt`.
- Update-answers skill: project skill at `.cursor/skills/update-answers/` refreshes `docs/answers.txt` from `docs/learnings.md` and the current codebase.
- Future enhancements location: use `docs/future.md`.
- Update-future skill: project skill at `.cursor/skills/update-future/` scans the whole repository, then refreshes `docs/future.md` with prioritized enhancement suggestions.
- Repository lifecycle: support `DELETE /api/v1/repositories/{id}` (DB row + clone directory + cascade cleanup hooks) and `POST /api/v1/repositories/{id}/reindex` (clear derived indexes, re-clone synchronously, call re-embed stub).
- Cascade cleanup hooks: Qdrant/graph/re-embed hooks live in `backend/services/cleanup_hooks.py` as no-op log stubs until those stores are wired.
- Frontend API layout: use `src/api/` modules plus a shared Axios client in `src/lib/axios.ts`. Only add API modules for endpoints that exist (currently `repositories.ts` and `workspace.ts`); do not keep empty stubs for future domains like auth/chat.
- Day 4 parser engine: use `tree-sitter` for Golang, Python, JavaScript, and TypeScript.
- Day 4 extract scope: symbols only (functions, classes/types, methods, imports).
- Day 4 parse trigger: run automatically after a successful clone and after reindex.
- Day 4 persistence: store parsed files and symbols in PostgreSQL.
- Day 4 API/frontend scope: `GET /api/v1/repositories/{id}/symbols` and `GET /api/v1/repositories/{id}/parse-summary`; parse summary shown in a modal on the repositories dashboard.
- Parse summary on repositories dashboard: show file/symbol/skipped counts per repo via `GET /api/v1/repositories/{id}/parse-summary`.
- Skipped files in parse summary: persist skipped paths + reason in `repository_skipped_files` and surface them in parse-summary / symbols responses.