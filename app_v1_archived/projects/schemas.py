from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    provider: str
    display_name: str


class StoryCreate(BaseModel):
    idea: str = Field(min_length=1, max_length=10_000)
    title: str | None = Field(default=None, max_length=200)


class StoryResponse(BaseModel):
    id: str
    title: str
    idea: str
    status: str
    version: int
    updated_at: datetime


class GenerationCreate(BaseModel):
    action: Literal["generate_concept", "generate_blueprint", "generate_chapter_plan"]
    parameters: dict[str, Any] = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    id: str
    action: str
    status: str
    output: dict[str, Any] | None
    failure_code: str | None


class ArtifactUpdate(BaseModel):
    payload: dict[str, Any]
    layer: Literal["baseline"] = "baseline"
    locked_paths: list[str] = Field(default_factory=list)
    expected_version: int = Field(ge=1)
    status: Literal["draft", "confirmed"] = "confirmed"


class BlueprintArtifactUpdate(ArtifactUpdate):
    layer: Literal["baseline", "living"] = "baseline"


class EntityCreate(BaseModel):
    type: Literal["character", "location", "organization", "item", "world_rule"]
    name: str = Field(min_length=1, max_length=200)
    canonical_data: dict[str, Any] = Field(default_factory=dict)
    lock_state: Literal["unlocked", "locked"] = "unlocked"


class EntityResponse(EntityCreate):
    id: str
    version: int
    updated_at: datetime


class EntityUpdate(BaseModel):
    canonical_data: dict[str, Any]
    lock_state: Literal["unlocked", "locked"]
    expected_version: int = Field(ge=1)


class StateEntryCreate(BaseModel):
    domain: Literal["character", "world", "timeline"]
    subject_id: str | None = None
    path: str = Field(min_length=1, max_length=200)
    value: Any
    source_ref: dict[str, Any]
    temporal_scope: dict[str, Any]
    certainty: Literal["confirmed"]
    context_policy: Literal["always", "relevant_only", "blocked"]


class StateEntryResponse(StateEntryCreate):
    id: str
    updated_at: datetime


class StateEntriesResponse(BaseModel):
    character: list[StateEntryResponse]
    world: list[StateEntryResponse]
    timeline: list[StateEntryResponse]


class ArtifactResponse(BaseModel):
    id: str
    kind: str
    layer: str
    payload: dict[str, Any]
    status: str
    locked_paths: list[str]
    source_task_id: str | None
    version: int
    updated_at: datetime
