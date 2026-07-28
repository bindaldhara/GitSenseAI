from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class RepositoryCreate(BaseModel):
    url: HttpUrl = Field(description="Public GitHub repository URL")


class RepositoryResponse(BaseModel):
    id: int
    url: str
    full_name: str
    provider: str
    status: str
    clone_path: str
    default_branch: str | None
    created_at: datetime
    updated_at: datetime


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryResponse]
