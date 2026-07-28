from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, root
from config import settings

app = FastAPI(
    title=settings.app_name,
    description="Agentic Software Intelligence Platform",
    version=settings.app_version,
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
