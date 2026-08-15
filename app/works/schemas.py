"""Pydantic DTOs for the works API."""
from datetime import datetime
from pydantic import BaseModel, Field


class WorkCreate(BaseModel):
    title: str = Field(default="未命名故事", min_length=1, max_length=200)


class WorkResponse(BaseModel):
    id: str
    title: str
    stage: str
    idea_text: str
    cover_color: str
    progress_text: str
    version: int
    deleted_at: datetime | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class IdeaUpdate(BaseModel):
    idea_text: str = Field(max_length=2000)
    expected_version: int = Field(ge=1)


class TitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    expected_version: int = Field(ge=1)


class AIConfigUpdate(BaseModel):
    model: str = Field(min_length=1, max_length=100)
    temperature: float = Field(ge=0, le=1.5)
    reasoning_strength: str = Field(pattern="^(low|medium|high)$")
    expected_version: int = Field(ge=1)


class AIConfigResponse(BaseModel):
    story_id: str
    model: str
    temperature: float
    reasoning_strength: str
    version: int

    model_config = {"from_attributes": True}


class ModelResponse(BaseModel):
    provider: str
    name: str
    model: str
    supports_json: bool
    configured: bool


class ModelAvailabilityResponse(BaseModel):
    provider: str
    name: str
    model: str
    available: bool
    reason: str = ""
    latency_ms: float = 0


class ModelPromptProfileResponse(BaseModel):
    provider: str
    system_prompt: str
    version: int
    updated_at: datetime | None = None


class ModelPromptProfileUpdate(BaseModel):
    system_prompt: str = Field(max_length=12000)
    expected_version: int = Field(ge=0)
