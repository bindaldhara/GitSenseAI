SHELL := /bin/bash
NODE_VERSION := 22.12.0
FRONTEND_PORT := 5173
BACKEND_PORT := 8000
COMPOSE := docker compose

.PHONY: frontend backend start-gitsense-ai check-frontend-port check-backend-port docker-build docker-up docker-down docker-logs

check-frontend-port:
	@if lsof -tiTCP:$(FRONTEND_PORT) -sTCP:LISTEN >/dev/null; then \
		echo "Frontend port $(FRONTEND_PORT) is already in use. Stop the existing process first."; \
		exit 1; \
	fi

check-backend-port:
	@if lsof -tiTCP:$(BACKEND_PORT) -sTCP:LISTEN >/dev/null; then \
		echo "Backend port $(BACKEND_PORT) is already in use. Stop the existing process first."; \
		exit 1; \
	fi

frontend: check-frontend-port
	@zsh -lc 'source ~/.zshrc && \
		if ! command -v nvm >/dev/null; then \
			echo "nvm is not available in zsh. Open a terminal where Node $(NODE_VERSION) is active, or load nvm in ~/.zshrc."; \
			exit 1; \
		fi && \
		cd frontend && \
		nvm use $(NODE_VERSION) && \
		npm install && \
		exec npm run dev'

backend: check-backend-port
	@cd backend && \
	if [ ! -d .venv ]; then python3 -m venv .venv; fi && \
	source .venv/bin/activate && \
	pip install -r requirements.txt && \
	exec uvicorn main:app --reload

start-gitsense-ai: check-backend-port check-frontend-port
	@backend_pid=""; frontend_pid=""; \
	trap ' \
		if [ -n "$$backend_pid" ]; then kill $$backend_pid 2>/dev/null || true; fi; \
		if [ -n "$$frontend_pid" ]; then kill $$frontend_pid 2>/dev/null || true; fi; \
		wait 2>/dev/null || true; \
	' EXIT INT TERM; \
	$(MAKE) backend & backend_pid=$$!; \
	$(MAKE) frontend & frontend_pid=$$!; \
	wait

docker-build:
	$(COMPOSE) build

docker-up:
	$(COMPOSE) up --build

docker-down:
	$(COMPOSE) down

docker-logs:
	$(COMPOSE) logs -f
