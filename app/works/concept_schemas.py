"""Pydantic DTOs for Story Concept generation and confirmation."""
from typing import Any

from pydantic import BaseModel, Field


class ConceptGenerationRequest(BaseModel):
    action: str = Field(default="generate_concept", pattern="^generate_concept$")
    model: str | None = None


class ConceptUpdate(BaseModel):
    payload: dict[str, Any]
    locked_paths: list[str] = Field(default_factory=list)
    expected_version: int = Field(ge=1)


class ConceptConfirm(BaseModel):
    expected_version: int = Field(ge=1)


class ConceptResponse(BaseModel):
    id: str
    story_id: str
    kind: str
    layer: str
    payload: dict[str, Any]
    status: str
    version: int
    locked_paths: list[str]
    source_task_id: str | None
    updated_at: str


class GenerationTaskResponse(BaseModel):
    id: str
    story_id: str
    action: str
    status: str
    artifact_id: str | None = None
    model_snapshot: dict[str, Any]
    error_type: str | None = None
