"""Chapter Plan DTOs."""
from typing import Any
from pydantic import BaseModel, Field


class ChapterPlanGenerationRequest(BaseModel):
    action: str = Field(default="generate_chapter_plan", pattern="^generate_chapter_plan$")
    model: str | None = None


class ChapterResponse(BaseModel):
    id: str
    story_id: str
    ordinal: int
    title: str
    goal: str
    summary: str
    main_characters: list[str]
    arc_role: str
    plan_status: str
    access_status: str
    version: int
    stale_reason: str | None


class ChapterPlanUpdate(BaseModel):
    title: str | None = None
    goal: str | None = None
    summary: str | None = None
    main_characters: list[str] | None = None
    arc_role: str | None = None
    expected_version: int = Field(ge=1)
