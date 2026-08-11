from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(200))
    idea: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="idea_draft")
    active_chapter_ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class StoryArtifact(Base):
    __tablename__ = "story_artifacts"
    __table_args__ = (UniqueConstraint("story_id", "kind", "version", name="uq_artifact_story_kind_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id"))
    kind: Mapped[str] = mapped_column(String(40))
    layer: Mapped[str] = mapped_column(String(40), default="baseline")
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(40), default="candidate")
    locked_paths: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id"))
    target_type: Mapped[str] = mapped_column(String(40), default="story")
    action: Mapped[str] = mapped_column(String(80))
    input_ref: Mapped[dict] = mapped_column(JSON)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_snapshot: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint("story_id", "type", "name", name="uq_entity_story_type_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id"))
    type: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    canonical_data: Mapped[dict] = mapped_column(JSON, default=dict)
    lock_state: Mapped[str] = mapped_column(String(20), default="unlocked")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class StateEntry(Base):
    __tablename__ = "state_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id"))
    domain: Mapped[str] = mapped_column(String(20))
    subject_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    path: Mapped[str] = mapped_column(String(200))
    value: Mapped[object] = mapped_column(JSON)
    source_ref: Mapped[dict] = mapped_column(JSON)
    temporal_scope: Mapped[dict] = mapped_column(JSON)
    certainty: Mapped[str] = mapped_column(String(20))
    context_policy: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
