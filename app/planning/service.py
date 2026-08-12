"""Chapter Plan generation and activation service."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.model_adapter import build_adapters, extract_json
from app.planning.models import Chapter
from app.planning.schemas import ChapterPlanGenerationRequest, ChapterPlanUpdate
from app.works.concept_service import _model_for_config
from app.works.models import GenerationTask
from app.works.service import get_ai_config, get_story_or_404


def chapter_response(chapter: Chapter) -> dict[str, Any]:
    return {
        "id": chapter.id,
        "story_id": chapter.story_id,
        "ordinal": chapter.ordinal,
        "title": chapter.title,
        "goal": chapter.goal,
        "summary": chapter.summary,
        "main_characters": json.loads(chapter.main_characters),
        "arc_role": chapter.arc_role,
        "plan_status": chapter.plan_status,
        "access_status": chapter.access_status,
        "version": chapter.version,
        "stale_reason": chapter.stale_reason,
    }


def list_chapters(db: Session, story_id: str) -> list[Chapter]:
    get_story_or_404(db, story_id)
    return list(db.scalars(select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.ordinal)))


def get_chapter(db: Session, story_id: str, chapter_id: str) -> Chapter:
    chapter = db.scalar(select(Chapter).where(Chapter.id == chapter_id, Chapter.story_id == story_id))
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


def fallback_chapters(idea: str = "") -> list[dict[str, Any]]:
    """Deterministic placeholder plan derived from the author's idea.

    Never hard-codes demo story content; used only when no model adapter is available.
    """
    seed = (idea or "根据作者创意展开").strip()[:60]
    return [
        {"title": "开端", "goal": "建立主角与核心冲突的入口。", "summary": f"基于「{seed}」展开故事起点，引入主角处境与第一层矛盾。", "main_characters": [], "arc_role": "建立主线"},
        {"title": "展开", "goal": "推动主角迈出第一步。", "summary": "主角尝试解决问题，遭遇第一次阻力并获取关键线索。", "main_characters": [], "arc_role": "推进主线"},
        {"title": "转折", "goal": "揭示隐藏真相的一角。", "summary": "一次意外使主角重新评估目标，冲突升级。", "main_characters": [], "arc_role": "首次反转"},
        {"title": "深入", "goal": "扩大冲突范围。", "summary": "主角深入核心矛盾，关键人物立场发生变化。", "main_characters": [], "arc_role": "扩大冲突"},
        {"title": "危机", "goal": "将主角逼到抉择点。", "summary": "代价逐渐显现，主角必须做出重要选择。", "main_characters": [], "arc_role": "揭示伏笔"},
        {"title": "收束", "goal": "解决主线并留下回响。", "summary": "主角面对最终矛盾，完成主线并回应主题。", "main_characters": [], "arc_role": "收束"},
    ]


def generate_chapter_plan(db: Session, story_id: str, request: ChapterPlanGenerationRequest) -> list[Chapter]:
    story = get_story_or_404(db, story_id)
    if story.stage != "blueprint_confirmed":
        raise HTTPException(status_code=409, detail="Blueprint must be confirmed before Chapter Plan generation")
    config = get_ai_config(db, story_id)
    spec = _model_for_config(request.model or config.model)
    task = GenerationTask(story_id=story.id, action="generate_chapter_plan", target_type="story", model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False), input_ref=json.dumps({"story_id": story.id, "blueprint": "confirmed"}, ensure_ascii=False), status="running")
    db.add(task)
    db.flush()
    messages = [
        {"role": "system", "content": "你是小说章节规划助手。只返回合法 JSON 数组，每项必须包含 title、goal、summary、main_characters（数组）、arc_role。生成 6 章高层计划，不生成正文。"},
        {"role": "user", "content": f"根据已确认的故事蓝图生成章节计划。故事创意：{story.idea_text}"},
    ]
    try:
        adapter = build_adapters().get(spec.provider)
        if adapter:
            payload = extract_json(adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=True, max_tokens=8192))
        else:
            payload = fallback_chapters(story.idea_text)
        if not isinstance(payload, list) or not payload:
            raise ValueError("Chapter Plan response must be a non-empty array")
        old = list(db.scalars(select(Chapter).where(Chapter.story_id == story.id)))
        for chapter in old:
            db.delete(chapter)
        db.flush()
        chapters = []
        for ordinal, item in enumerate(payload, 1):
            chapter = Chapter(story_id=story.id, ordinal=ordinal, title=str(item.get("title", f"第 {ordinal} 章")), goal=str(item.get("goal", "")), summary=str(item.get("summary", "")), main_characters=json.dumps(item.get("main_characters", []), ensure_ascii=False), arc_role=str(item.get("arc_role", "")), plan_status="fixed" if ordinal == 1 else "outline", access_status="active" if ordinal == 1 else "locked")
            db.add(chapter)
            chapters.append(chapter)
        task.status = "succeeded"
        task.output_summary = json.dumps({"chapter_count": len(chapters)}, ensure_ascii=False)
        story.stage = "chapter_planning"
        story.progress_text = f"第 1 章 / {len(chapters)} 章"
        story.version += 1
        db.commit()
        for chapter in chapters:
            db.refresh(chapter)
        return chapters
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
        db.commit()
        raise HTTPException(status_code=502, detail="Chapter Plan generation failed; Blueprint remains unchanged") from exc


def update_chapter_plan(db: Session, story_id: str, chapter_id: str, data: ChapterPlanUpdate) -> Chapter:
    chapter = get_chapter(db, story_id, chapter_id)
    if chapter.access_status != "active":
        raise HTTPException(status_code=409, detail="Locked Chapter cannot be edited")
    if chapter.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Chapter version conflict")
    for field in ("title", "goal", "summary", "arc_role"):
        value = getattr(data, field)
        if value is not None:
            setattr(chapter, field, value)
    if data.main_characters is not None:
        chapter.main_characters = json.dumps(data.main_characters, ensure_ascii=False)
    chapter.version += 1
    db.commit()
    db.refresh(chapter)
    return chapter
