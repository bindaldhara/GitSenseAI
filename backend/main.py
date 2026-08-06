from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import admin, chat, diagram, graph, health, repositories, retrieval_lab, root
from config import settings
from db import initialize_database
from vector_store.qdrant_store import ensure_collection


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    ensure_collection()
    yield

app = FastAPI(
    title=settings.app_name,
    description="Agentic Software Intelligence Platform",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root.router)
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(repositories.router, prefix=settings.api_v1_prefix)
app.include_router(graph.router, prefix=settings.api_v1_prefix)
app.include_router(diagram.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(retrieval_lab.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
