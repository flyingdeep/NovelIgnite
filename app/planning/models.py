"""Chapter Plan persistence model."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.works.models import utc_now


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("story_id", "ordinal", name="uq_chapters_story_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    goal: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    main_characters: Mapped[str] = mapped_column(Text, default="[]")
    arc_role: Mapped[str] = mapped_column(String(100), default="")
    plan_status: Mapped[str] = mapped_column(String(30), default="outline")
    access_status: Mapped[str] = mapped_column(String(30), default="locked", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    stale_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class StateSnapshot(Base):
    """Entering-state snapshot for a chapter: characters/world/timeline, no future info."""

    __tablename__ = "state_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), unique=True, index=True)
    based_on_chapter_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    state: Mapped[str] = mapped_column(Text, default="{}")
    state_hash: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(20), default="valid")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ChapterEvent(Base):
    """A planned/progressed event in a chapter. planned_result vs actual_result separated."""

    __tablename__ = "chapter_events"
    __table_args__ = (UniqueConstraint("chapter_id", "ordinal", name="uq_events_chapter_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200), default="")
    related_characters: Mapped[str] = mapped_column(Text, default="[]")
    related_locations: Mapped[str] = mapped_column(Text, default="[]")
    goal: Mapped[str] = mapped_column(Text, default="")
    planned_result: Mapped[str] = mapped_column(Text, default="")
    actual_result: Mapped[str] = mapped_column(Text, default="")
    impact: Mapped[str] = mapped_column(Text, default="")
    arc_role: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Scene(Base):
    """A scene within a chapter; unit of chapter-level planning and prose generation."""

    __tablename__ = "scenes"
    __table_args__ = (UniqueConstraint("chapter_id", "ordinal", name="uq_scenes_chapter_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200), default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    time: Mapped[str] = mapped_column(String(100), default="")
    pov: Mapped[str] = mapped_column(String(100), default="")
    character_goals: Mapped[str] = mapped_column(Text, default="")
    conflict: Mapped[str] = mapped_column(Text, default="")
    key_events: Mapped[str] = mapped_column(Text, default="")
    scene_result: Mapped[str] = mapped_column(Text, default="")
    chapter_goal_relation: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="planned")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Beat(Base):
    """A beat within a scene; smallest unit of prose generation."""

    __tablename__ = "beats"
    __table_args__ = (UniqueConstraint("scene_id", "ordinal", name="uq_beats_scene_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200), default="")
    instruction: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="planned")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ProseVersion(Base):
    """Append-only Markdown prose version for a beat."""

    __tablename__ = "prose_versions"
    __table_args__ = (UniqueConstraint("beat_id", "version", name="uq_prose_beat_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    beat_id: Mapped[str] = mapped_column(ForeignKey("beats.id", ondelete="CASCADE"), index=True)
    markdown: Mapped[str] = mapped_column(Text, default="")
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="candidate")
    applied_by: Mapped[str] = mapped_column(String(30), default="ai")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class StateDelta(Base):
    """State changes produced at a beat/scene/chapter checkpoint."""

    __tablename__ = "state_deltas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    scope_type: Mapped[str] = mapped_column(String(20))  # beat / scene / chapter
    scope_id: Mapped[str] = mapped_column(String(36))
    source_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    changes: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="proposed")
    check_result: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ConsistencyIssue(Base):
    """Consistency findings at a beat/scene/chapter checkpoint."""

    __tablename__ = "consistency_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    checkpoint: Mapped[str] = mapped_column(String(20), default="beat")  # beat / scene / chapter
    scope_id: Mapped[str] = mapped_column(String(36))
    rule: Mapped[str] = mapped_column(String(120), default="")
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    evidence: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
