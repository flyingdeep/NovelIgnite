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
