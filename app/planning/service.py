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


def fallback_chapters() -> list[dict[str, Any]]:
    return [
        {"title": "消失的委托人", "goal": "接受委托，发现三年记忆缺口是人为造成。", "summary": "林墨收到匿名委托与异常样本，回到档案室寻找事故记录。", "main_characters": ["林墨"], "arc_role": "建立身份谜题"},
        {"title": "拍卖目录", "goal": "进入地下市场，找到与自己有关的记忆样本。", "summary": "林墨根据邀请函潜入地下拍卖会，发现拍卖目录中的样本编号属于自己。", "main_characters": ["林墨", "乔岚"], "arc_role": "推进身份谜题"},
        {"title": "记忆样本", "goal": "验证样本来源，确认记忆缺口的异常性质。", "summary": "样本中的细节与林墨的专业记忆冲突，迫使他重新审视事故。", "main_characters": ["林墨", "乔岚"], "arc_role": "首次反转"},
        {"title": "监管者来信", "goal": "让官方势力介入并提高调查风险。", "summary": "沈砚发来警告，要求林墨停止调查三年前事故。", "main_characters": ["林墨", "沈砚"], "arc_role": "扩大冲突"},
        {"title": "损坏的证词", "goal": "从衰减记忆中拼合事故前夜的片段。", "summary": "林墨发现被损坏的证词仍保留一个不该存在的时间标记。", "main_characters": ["林墨"], "arc_role": "揭示伏笔"},
        {"title": "双重委托", "goal": "暴露乔岚的隐瞒，制造核心关系危机。", "summary": "乔岚承认自己接受了另一份委托，林墨必须决定是否继续合作。", "main_characters": ["林墨", "乔岚"], "arc_role": "关系反转"},
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
            payload = fallback_chapters()
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
