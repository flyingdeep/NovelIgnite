from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChapterPlanGenerate(BaseModel):
    provider: str | None = None
    chapter_count: int = Field(default=6, ge=2, le=24)


class ChapterCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ordinal: int
    title: str
    summary: str
    goal: str
    main_characters: list[str]
    arc_relation: str
    plan_status: str
    access_status: str
    stale_reason: str | None
    version: int
    updated_at: datetime


class ChapterOutlineUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    main_characters: list[str] = Field(default_factory=list)
    arc_relation: str = ""
    expected_version: int = Field(ge=1)


class ChapterWorkspaceResponse(BaseModel):
    chapter: ChapterCard
    message: str
