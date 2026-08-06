from typing import Literal

from pydantic import BaseModel, Field

from schemas.chat import RetrievedSource


class DiagramRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    diagram_type: Literal["auto", "dependency", "architecture"] = "auto"
    limit: int = Field(default=50, ge=1, le=200)


class DiagramResponse(BaseModel):
    repository_id: int
    question: str
    diagram_type: Literal["dependency", "architecture"]
    title: str
    description: str
    mermaid: str
    model: str = ""
    sources: list[RetrievedSource] = Field(default_factory=list)
