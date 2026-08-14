"""Pydantic DTOs for Phase 5 Chapter Workspace: context, events, scenes, beats."""
from typing import Any

from pydantic import BaseModel, Field


# --- Chapter Context ---

class StateSnapshotResponse(BaseModel):
    chapter_id: str
    based_on_chapter_id: str | None
    state: dict[str, Any]
    state_hash: str
    status: str


class ChapterEventResponse(BaseModel):
    id: str
    chapter_id: str
    ordinal: int
    title: str
    related_characters: list[str]
    related_locations: list[str]
    goal: str
    planned_result: str
    actual_result: str
    impact: str
    arc_role: str
    version: int


class BeatResponse(BaseModel):
    id: str
    scene_id: str
    ordinal: int
    name: str
    instruction: str
    status: str
    version: int


class SceneResponse(BaseModel):
    id: str
    chapter_id: str
    ordinal: int
    title: str
    location: str
    time: str
    pov: str
    character_goals: str
    conflict: str
    key_events: str
    scene_result: str
    chapter_goal_relation: str
    status: str
    version: int
    beats: list[BeatResponse] = Field(default_factory=list)


class ChapterContextResponse(BaseModel):
    chapter: dict[str, Any]
    snapshot: StateSnapshotResponse | None
    events: list[ChapterEventResponse]
    scenes: list[SceneResponse]


# --- Updates ---

class ChapterEventUpdate(BaseModel):
    title: str | None = None
    related_characters: list[str] | None = None
    related_locations: list[str] | None = None
    goal: str | None = None
    planned_result: str | None = None
    actual_result: str | None = None
    impact: str | None = None
    arc_role: str | None = None
    expected_version: int = Field(ge=1)


class SceneUpdate(BaseModel):
    title: str | None = None
    location: str | None = None
    time: str | None = None
    pov: str | None = None
    character_goals: str | None = None
    conflict: str | None = None
    key_events: str | None = None
    scene_result: str | None = None
    chapter_goal_relation: str | None = None
    status: str | None = None
    expected_version: int = Field(ge=1)


class BeatUpdate(BaseModel):
    name: str | None = None
    instruction: str | None = None
    status: str | None = None
    expected_version: int = Field(ge=1)


class ScenePlanGenerationRequest(BaseModel):
    action: str = Field(default="generate_scene_plan", pattern="^(generate_scene_plan|generate_beat_plan|generate_scene|generate_chapter_remaining|regenerate_beat|generate_beat)$")
    model: str | None = None
    beat_id: str | None = None


# --- Phase 6: prose versions, deltas, consistency ---

class ProseVersionCreate(BaseModel):
    markdown: str = Field(min_length=1)
    applied_by: str = Field(default="author", pattern="^(author|ai)$")
    expected_version: int = Field(ge=1)


class ProseVersionResponse(BaseModel):
    id: str
    story_id: str
    chapter_id: str
    scene_id: str
    beat_id: str
    markdown: str
    parent_id: str | None
    version: int
    status: str
    applied_by: str


class DeltaResponse(BaseModel):
    id: str
    story_id: str
    chapter_id: str
    scope_type: str
    scope_id: str
    source_version_id: str | None
    changes: dict[str, Any]
    status: str
    check_result: dict[str, Any]


class ConsistencyIssueResponse(BaseModel):
    id: str
    story_id: str
    chapter_id: str
    checkpoint: str
    scope_id: str
    rule: str
    severity: str
    evidence: str
    status: str


class ChapterDeltaConfirm(BaseModel):
    expected_delta_id: str | None = None
