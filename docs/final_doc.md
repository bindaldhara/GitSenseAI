# GitSense AI - Agentic Software Intelligence Platform

## Project Overview

GitSense AI is a production-grade AI platform capable of understanding, indexing, and reasoning over large-scale software repositories. It enables developers to interact with codebases using natural language and provides architectural insights, dependency analysis, documentation generation, and intelligent code discovery.

The project combines modern AI engineering concepts such as Multi-Agent RAG, Graph RAG, MCP-compatible tools, semantic caching, and real-time GitHub indexing with production-grade infrastructure using Docker and Kubernetes.

## Project Goal

Build an AI-powered platform that can:

- Understand any GitHub repository.
- Explain repository architecture.
- Perform semantic code search.
- Generate documentation automatically.
- Analyze dependencies and service relationships.
- Suggest code improvements.
- Support real-time indexing on repository changes.
- Execute MCP-compatible tools.
- Scale to repositories with 100K+ lines of code.

## Tech Stack

### Frontend

- React
- Vite
- Tailwind CSS
- Shadcn UI
- React Query
- React Markdown
- Socket.io

### Backend

- FastAPI
- Python 3.12
- Celery
- AsyncIO

### AI Stack

- LangGraph
- LangChain
- OpenAI GPT
- Ollama (Optional)
- Sentence Transformers

### Retrieval

- Qdrant
- BM25
- Hybrid Search
- Graph RAG

### Databases

- PostgreSQL
- Redis

### DevOps

- Docker
- Docker Compose
- Kubernetes
- GitHub Actions
- Nginx

### Monitoring

- Prometheus
- Grafana
- LangSmith

## High-Level Architecture

```text
                   User
                      |
                      v
             React + Tailwind
                      |
                      v
                  FastAPI
                      |
                      v
               Router Agent
                      |
      ------------------------------------
      |          |           |           |
      v          v           v           v
 Code Agent   Docs Agent  Graph Agent  Arch Agent
      |          |           |           |
      ------------------------------------
                      |
                      v
               MCP Tool Layer
                      |
      -----------------------------------
      |         |          |            |
 Clone Repo  Search File  Run Tests  Generate Docs
      |
      v
   GitHub
      |
      v
 Real-Time Webhooks
      |
      v
Incremental Indexing
      |
      v
Qdrant + Graph DB + Redis
```

## Core Features

### Repository Management

- Add GitHub repositories using URL.
- Index repositories.
- Re-index repositories.
- Delete repositories.
- Support multiple repositories.
- Repository metadata management.

### Intelligent Code Search

Users can ask:

- How does authentication work?
- Where is Redis being used?
- Explain the payment workflow.
- Find all usages of UserService.
- Which APIs are exposed?

Capabilities:

- Semantic search.
- Function-level search.
- File-level search.
- Language filtering.
- Directory filtering.

### Repository Understanding

- Architecture explanation.
- Service dependency analysis.
- API flow explanation.
- Database mapping.
- Repository summarization.

### Documentation Generation

Generate:

- README.md
- API Documentation
- Service Documentation
- Function Summaries
- Onboarding Guides

### Chat Experience

- Streaming responses.
- Markdown rendering.
- Chat history.
- Conversation memory.
- Multi-session support.

### Visualization

Generate:

- Mermaid diagrams.
- Architecture diagrams.
- Service dependency graphs.
- Data flow diagrams.

### Multi-Repository Support

- Compare repositories.
- Search across repositories.
- Organization-level code understanding.

## Advanced Features

### 1. Agentic RAG

Agents:

- Router Agent
- Code Agent
- Documentation Agent
- Architecture Agent
- Graph Agent

Examples:

- Explain authentication.
- Generate README.
- Suggest refactoring opportunities.
- Explain architecture.

### 2. Graph RAG

Build a knowledge graph for:

- Services
- APIs
- Classes
- Functions
- Databases
- External dependencies

Capabilities:

- Dependency analysis.
- Impact analysis.
- Service mapping.
- Relationship discovery.

### 3. MCP Tool Integration

Implemented MCP-compatible tools:

- `clone_repo()`
- `search_file()`
- `run_tests()`
- `generate_docs()`
- `summarize_repo()`
- `analyze_dependencies()`
- `find_dead_code()`

### 4. Hybrid Search

Combines:

- BM25
- Vector Search

Benefits:

- Better retrieval quality.
- Improved relevance.
- Reduced hallucinations.

### 5. Semantic Caching

- Redis-based semantic cache.

Benefits:

- Faster responses.
- Reduced token usage.
- Lower AI costs.

### 6. Real-Time GitHub Indexing

Pipeline:

```text
GitHub Webhook
      ↓
Push Event
      ↓
Changed Files
      ↓
Generate Embeddings
      ↓
Update Qdrant
```

Features:

- Near real-time updates.
- Incremental indexing.
- Automatic synchronization.

### 7. AI Observability

Track:

- Token usage.
- Cost per request.
- Latency.
- Cache hit ratio.
- Hallucination rate.
- Agent execution time.

Tools:

- LangSmith
- Prometheus
- Grafana

### 8. Production Features

- JWT Authentication.
- Role-based access.
- CI/CD.
- Monitoring.
- Logging.
- Error tracking.

### 9. Scalability Features

- Dockerized services.
- Kubernetes deployment.
- Horizontal scaling.
- Background workers.
- Asynchronous processing.

### 10. Future Enhancements

- VS Code Extension.
- Slack Integration.
- GitHub App.
- Voice Interface.
- AI Pull Request Reviewer.
- Automated Unit Test Generation.
- Security Vulnerability Detection.

## Project Folder Structure

```text
frontend/

backend/
    api/
    agents/
    rag/
    graph_rag/
    services/
    workers/
    vector_store/
    db/
    cache/
    tools/

k8s/
docker/
.github/
```

## WEEK 1 - Build the MVP

### Goal

Develop the complete RAG foundation.

### Day 1

Setup React + Tailwind.
Setup FastAPI.
Setup Docker Compose.
Initialize repositories.

### Day 2

Setup:
PostgreSQL
Redis
Qdrant

### Day 3

Build:
GitHub URL submission API.
Repository cloning service.

### Day 4

Build parsers for:
Golang
Python
JavaScript
TypeScript

### Day 5

Implement:
Chunking.
Embeddings.
Qdrant ingestion.

### Day 6

Implement:
Chat API.
Retrieval.
Response generation.

### Day 7

Frontend:
Chat UI.
Repository dashboard.
Markdown support.

### Deliverables

- Repository indexing.
- Basic RAG.
- Chat UI.
- End-to-end MVP.

## WEEK 2 - Production AI Features

### Goal

Introduce advanced AI capabilities.

### Day 8

Implement:
Hybrid Search.

### Day 9

Implement:
Semantic Caching.
Cache analytics.

### Day 10

Implement:
LangGraph.
Router Agent.
Code Agent.

### Day 11

Implement:
Documentation Agent.
Architecture Agent.

### Day 12

Implement:
Graph RAG.
Dependency mapping.

### Day 13

Implement:
Mermaid diagram generation.

### Day 14

Implement:
JWT Authentication.
Chat history.
Multi-repository support.

### Deliverables

- Multi-Agent System.
- Graph RAG.
- Authentication.
- Hybrid Search.
- Semantic Cache.

## WEEK 3 - Differentiators

### Goal

Build features that make the project stand out.

### Day 15

Implement MCP tools:

- `clone_repo()`
- `generate_docs()`
- `run_tests()`

### Day 16

Implement:
`search_file()`
`summarize_repo()`
`find_dead_code()`

### Day 17

Implement:
GitHub Webhooks.

Supported Events:

- Push
- Pull Request
- Merge

### Day 18

Implement:
Incremental Indexing.
Real-time embedding updates.

### Day 19

Implement AI Observability:
Token tracking.
Latency monitoring.
Cost tracking.
Agent execution tracking.

### Day 20

Deployment:
Docker.
Kubernetes.
GitHub Actions.

### Day 21

Final Polish:
README.
Demo Video.
Architecture Diagram.
LinkedIn Post.
Resume Bullets.

### Deliverables

- MCP Tool Layer.
- Real-Time GitHub Indexing.
- AI Monitoring.
- Kubernetes Deployment.
- Production Release.

## Final Deliverables

### AI

- Agentic RAG
- Graph RAG
- Hybrid Search
- Semantic Search
- Semantic Caching

### Agents

- Router Agent
- Code Agent
- Documentation Agent
- Architecture Agent
- Graph Agent

### MCP Tools

- Clone Repository
- Search Files
- Run Tests
- Generate Documentation
- Summarize Repository
- Detect Dead Code

### GitHub

- Webhooks
- Incremental Indexing
- Multi-Repository Support

### Infrastructure

- Docker
- Kubernetes
- CI/CD
- Monitoring

## Key Differentiators

- Multi-Agent Architecture.
- Agentic RAG.
- Graph RAG.
- MCP Tool Integration.
- Real-Time GitHub Indexing.
- Semantic Caching.
- Hybrid Search.
- AI Observability.
- Kubernetes Deployment.
- Production-Grade Infrastructure.

## Resume Highlights

- Built GitSense AI, a production-grade Agentic Software Intelligence Platform leveraging Multi-Agent RAG, Graph RAG, and MCP-compatible tools to analyze repositories containing 100K+ lines of code.
- Implemented hybrid retrieval (BM25 + vector search) with semantic caching, reducing average response latency by over 60%.
- Developed a real-time GitHub indexing pipeline using GitHub webhooks and incremental embeddings.
- Designed a multi-agent architecture using LangGraph with specialized agents for code analysis, documentation generation, and architectural reasoning.
- Containerized and deployed the platform using Docker, Kubernetes, GitHub Actions, Prometheus, and Grafana.

## Project Summary

GitSense AI is a production-grade Agentic Software Intelligence Platform that leverages Multi-Agent RAG, Graph RAG, MCP-compatible tools, semantic caching, and real-time GitHub indexing to understand, analyze, and reason over large-scale software repositories. The platform empowers developers to interact with codebases using natural language while providing architectural insights, dependency analysis, documentation generation, and intelligent code discovery capabilities.

`Cursor helps developers understand code. GitSense helps engineering teams understand systems.`

- Cursor operates at the code level.
- GitSense operates at the system level.

## Capability Comparison

| Capabilities | Cursor IDE | GitSense AI |
| --- | --- | --- |
| Real-Time Push-Based Indexing | Local re-indexing when files open/save locally. | GitHub Webhook Listeners that incrementally update embeddings immediately upon git push on remote branches. |
| Automatic Visual Architecture Mapping | Generates inline text or code diffs. | Generates live Mermaid.js diagrams, system flowcharts, and service-dependency maps for architecture docs. |
| Centralized System-Wide Hub | Scope is tied to local developer workspaces or open folders. | Operates as an enterprise web hub, letting managers, leads, and onboarding engineers query total system architecture. |
| Exposed as an MCP Server | Client/Consumer of tools and MCP servers. | Acts as the MCP Context Provider for other tools (you can plug GitSense into Cursor as an MCP server to grant Cursor full architectural awareness). |
