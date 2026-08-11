from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.planning.models import Chapter
from app.projects.models import Story
from app.projects.service import ConflictError, NotFoundError, ProjectService


class ChapterPlanningService:
    def __init__(self, session: Session, projects: ProjectService) -> None:
        self.session = session
        self.projects = projects

    def _story(self, story_id: str) -> Story:
        return self.projects.get_story(story_id)

    def generate_plan(self, story_id: str, provider: str | None, chapter_count: int) -> list[Chapter]:
        story = self._story(story_id)
        if story.status != "blueprint_confirmed":
            raise ConflictError()
        existing = self.list_chapters(story_id)
        if existing:
            raise ConflictError()
        parameters: dict[str, Any] = {"chapter_count": chapter_count}
        if provider:
            parameters["provider"] = provider
        task = self.projects._generate(story_id, "generate_chapter_plan", parameters)
        raw_plan = task.output.get("chapters") if task.output else None
        if not isinstance(raw_plan, list) or len(raw_plan) < 2:
            raise ConflictError()
        chapters: list[Chapter] = []
        for index, item in enumerate(raw_plan, start=1):
            if not isinstance(item, dict):
                raise ConflictError()
            chapter = Chapter(
                story_id=story_id,
                ordinal=index,
                title=str(item.get("title") or f"第 {index} 章"),
                summary=str(item.get("summary") or item.get("core_event") or "待作者完善的章节雏形。"),
                goal=str(item.get("goal") or "推进主线剧情。"),
                main_characters=item.get("main_characters") if isinstance(item.get("main_characters"), list) else [],
                arc_relation=str(item.get("arc_relation") or "推进故事主线。"),
                plan_status="fixed" if index == 1 else "outline",
                access_status="active" if index == 1 else "locked",
            )
            chapters.append(chapter)
            self.session.add(chapter)
        story.status = "chapter_planning"
        story.active_chapter_ordinal = 1
        self.session.commit()
        for chapter in chapters:
            self.session.refresh(chapter)
        return chapters

    def list_chapters(self, story_id: str) -> list[Chapter]:
        self._story(story_id)
        return self.session.scalars(
            select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.ordinal)
        ).all()

    def get_chapter(self, chapter_id: str) -> Chapter:
        chapter = self.session.get(Chapter, chapter_id)
        if chapter is None:
            raise NotFoundError()
        return chapter

    def update_outline(self, chapter_id: str, **data: Any) -> Chapter:
        chapter = self.get_chapter(chapter_id)
        if chapter.access_status not in {"locked", "active"} or chapter.plan_status == "fixed":
            raise ConflictError()
        if chapter.version != data.pop("expected_version"):
            raise ConflictError()
        for field in ("title", "summary", "goal", "main_characters", "arc_relation"):
            setattr(chapter, field, data[field])
        chapter.plan_status = "revised"
        chapter.version += 1
        self.session.commit()
        self.session.refresh(chapter)
        return chapter

    def assert_active(self, chapter_id: str) -> Chapter:
        chapter = self.get_chapter(chapter_id)
        if chapter.access_status != "active":
            raise ConflictError()
        return chapter
