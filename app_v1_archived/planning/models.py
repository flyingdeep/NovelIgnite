from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.projects.models import utc_now


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("story_id", "ordinal", name="uq_chapter_story_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id"))
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    goal: Mapped[str] = mapped_column(Text)
    main_characters: Mapped[list[str]] = mapped_column(JSON, default=list)
    arc_relation: Mapped[str] = mapped_column(Text, default="")
    plan_status: Mapped[str] = mapped_column(String(20))
    access_status: Mapped[str] = mapped_column(String(20))
    stale_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
