"""Pydantic DTOs for Blueprint baseline and living state."""
from typing import Any
from pydantic import BaseModel, Field

BLUEPRINT_KINDS = ("bible", "characters", "world", "timeline", "arc", "living_state")


class BlueprintGenerationRequest(BaseModel):
    action: str = Field(default="generate_blueprint", pattern="^generate_blueprint$")
    model: str | None = None


class BlueprintUpdate(BaseModel):
    payload: dict[str, Any]
    locked_paths: list[str] = Field(default_factory=list)
    expected_version: int = Field(ge=1)


class BlueprintConfirm(BaseModel):
    expected_versions: dict[str, int] = Field(default_factory=dict)


def artifact_response(artifact) -> dict[str, Any]:
    import json
    return {
        "id": artifact.id,
        "story_id": artifact.story_id,
        "kind": artifact.kind,
        "layer": artifact.layer,
        "payload": json.loads(artifact.payload),
        "status": artifact.status,
        "version": artifact.version,
        "locked_paths": json.loads(artifact.locked_paths),
        "source_task_id": artifact.source_task_id,
        "updated_at": artifact.updated_at.isoformat(),
    }
