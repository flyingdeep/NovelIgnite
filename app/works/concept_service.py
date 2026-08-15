"""Story Concept application service."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.model_adapter import ModelSpec, build_adapters
from app.infrastructure.model_prompt_profiles import compose_system_prompt
from app.infrastructure.prompts import prompt_version, system_prompt
from app.works.concept_schemas import ConceptConfirm, ConceptGenerationRequest, ConceptUpdate
from app.works.models import GenerationTask, StoryArtifact
from app.works.service import get_ai_config, get_story_or_404

CONCEPT_KIND = "concept"


def _payload(artifact: StoryArtifact) -> dict[str, Any]:
    return json.loads(artifact.payload)


def _locked(artifact: StoryArtifact) -> list[str]:
    return json.loads(artifact.locked_paths)


def latest_concept(db: Session, story_id: str) -> StoryArtifact | None:
    return db.scalar(select(StoryArtifact).where(StoryArtifact.story_id == story_id, StoryArtifact.kind == CONCEPT_KIND).order_by(StoryArtifact.version.desc()))


def concept_response(artifact: StoryArtifact) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "story_id": artifact.story_id,
        "kind": artifact.kind,
        "layer": artifact.layer,
        "payload": _payload(artifact),
        "status": artifact.status,
        "version": artifact.version,
        "locked_paths": _locked(artifact),
        "source_task_id": artifact.source_task_id,
        "updated_at": artifact.updated_at.isoformat(),
    }


def _model_for_config(model_name: str | None) -> ModelSpec:
    from app.infrastructure.model_adapter import configured_model_specs

    specs = configured_model_specs()
    if model_name:
        for spec in specs:
            if spec.name == model_name or spec.provider == model_name or spec.model == model_name:
                return spec
    return next(spec for spec in specs if spec.name == "DeepSeek V4 Flash")


def _normalize_concept_payload(payload: Any) -> dict[str, Any]:
    """Normalize LLM concept output so the stored artifact always has a stable shape.

    Guards against model output drift (e.g. selling_points as a semicolon-separated
    string instead of a list) that could otherwise leak stale front-end demo data.
    """
    if not isinstance(payload, dict):
        payload = _fallback_concept("")
    selling = payload.get("selling_points")
    if isinstance(selling, str):
        payload["selling_points"] = [part.strip() for part in re.split(r"[；;\n]", selling) if part.strip()]
    if not isinstance(payload.get("selling_points"), list):
        payload["selling_points"] = []
    return payload


def _fallback_concept(idea: str) -> dict[str, Any]:
    return {
        "genre": "待作者确定",
        "style": "待作者确定",
        "length": "待作者确定",
        "viewpoint": "待作者确定",
        "summary": idea or "请先输入创作意图。",
        "theme": "故事希望讨论的核心问题，等待 AI 与作者共同明确。",
        "conflict": "主角目标与阻力，等待进一步展开。",
        "selling_points": ["由作者原始创意继续展开", "保留作者对风格和重点的最终决定权"],
    }


def generate_concept(db: Session, story_id: str, request: ConceptGenerationRequest) -> tuple[StoryArtifact, GenerationTask]:
    story = get_story_or_404(db, story_id)
    if not story.idea_text.strip():
        raise HTTPException(status_code=422, detail="Idea text is required before concept generation")
    config = get_ai_config(db, story_id)
    spec = _model_for_config(request.model or config.model)
    task = GenerationTask(
        story_id=story.id,
        action="generate_concept",
        target_type="story",
        model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False),
        prompt_version=prompt_version("generate_concept"),
        input_ref=json.dumps({"story_id": story.id, "idea_length": len(story.idea_text)}, ensure_ascii=False),
        status="running",
    )
    db.add(task)
    db.flush()
    messages = [
        {"role": "system", "content": compose_system_prompt(db, spec.provider, "generate_concept")},
        {"role": "user", "content": f"请根据作者创意生成 Story Concept 候选。保留作者意图，不要把未确认内容当事实。作者创意：{story.idea_text}"},
    ]
    try:
        adapters = build_adapters()
        adapter = adapters.get(spec.provider)
        if adapter is None:
            payload = _fallback_concept(story.idea_text)
        else:
            raw = adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=True, action="generate_concept")
            from app.infrastructure.model_adapter import extract_json
            payload = _normalize_concept_payload(extract_json(raw))
        previous = latest_concept(db, story.id)
        artifact = StoryArtifact(
            story_id=story.id,
            kind=CONCEPT_KIND,
            layer="baseline",
            payload=json.dumps(payload, ensure_ascii=False),
            status="candidate",
            version=(previous.version + 1 if previous else 1),
            locked_paths=json.dumps(_locked(previous) if previous else [], ensure_ascii=False),
            source_task_id=task.id,
        )
        db.add(artifact)
        db.flush()
        task.status = "succeeded"
        task.target_id = artifact.id
        task.output_summary = json.dumps({"field_count": len(payload), "text_length": len(raw) if adapter else 0}, ensure_ascii=False)
        story.stage = "idea_locked"
        story.version += 1
        db.commit()
        db.refresh(artifact)
        db.refresh(task)
        return artifact, task
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
        db.commit()
        raise HTTPException(status_code=502, detail="Concept generation failed; original Idea is unchanged") from exc


def update_concept(db: Session, story_id: str, data: ConceptUpdate) -> StoryArtifact:
    get_story_or_404(db, story_id)
    current = latest_concept(db, story_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    if current.status == "confirmed":
        raise HTTPException(status_code=409, detail="Confirmed Concept cannot be edited directly")
    if current.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Concept version conflict")
    locked = set(_locked(current))
    for path in locked:
        if data.payload.get(path) != _payload(current).get(path):
            raise HTTPException(status_code=409, detail=f"Locked Concept field cannot be changed: {path}")
    artifact = StoryArtifact(
        story_id=story_id,
        kind=CONCEPT_KIND,
        layer="baseline",
        payload=json.dumps(data.payload, ensure_ascii=False),
        status="candidate",
        version=current.version + 1,
        locked_paths=json.dumps(sorted(locked | set(data.locked_paths)), ensure_ascii=False),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def _generate_title_if_unnamed(db: Session, story) -> None:
    """After Concept confirmation, auto-generate a working title if the story is still unnamed.

    Never fails the confirm flow: on any error the default title is kept and the author
    can still rename via the title endpoint.
    """
    if story.title and not story.title.startswith("未命名故事"):
        return
    config = get_ai_config(db, story.id)
    spec = _model_for_config(config.model)
    task = GenerationTask(
        story_id=story.id,
        action="generate_title",
        target_type="story",
        model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False),
        prompt_version=prompt_version("generate_title"),
        input_ref=json.dumps({"story_id": story.id}, ensure_ascii=False),
        status="running",
    )
    db.add(task)
    db.flush()
    try:
        adapters = build_adapters()
        adapter = adapters.get(spec.provider)
        concept = latest_concept(db, story.id)
        payload = _payload(concept) if concept else {}
        messages = [
            {"role": "system", "content": compose_system_prompt(db, spec.provider, "generate_title")},
            {"role": "user", "content": (
                f"题材：{payload.get('genre', '')}\n"
                f"风格：{payload.get('style', '')}\n"
                f"篇幅：{payload.get('length', '')}\n"
                f"故事梗概：{payload.get('summary', '')}\n"
                f"主题：{payload.get('theme', '')}"
            )},
        ]
        title = None
        if adapter is not None:
            raw = adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=True, action="generate_title")
            from app.infrastructure.model_adapter import extract_json
            title = str(extract_json(raw).get("title", "")).strip()
        if title:
            story.title = title[:200]
            story.version += 1
            task.status = "succeeded"
            task.output_summary = json.dumps({"title": story.title}, ensure_ascii=False)
        else:
            task.status = "failed"
            task.error_type = "empty_title"
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
    db.commit()


def confirm_concept(db: Session, story_id: str, data: ConceptConfirm) -> StoryArtifact:
    story = get_story_or_404(db, story_id)
    current = latest_concept(db, story_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    if current.status == "confirmed":
        raise HTTPException(status_code=409, detail="Concept is already confirmed")
    if current.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Concept version conflict")
    current.status = "confirmed"
    story.stage = "concept_confirmed"
    story.version += 1
    db.commit()
    try:
        _generate_title_if_unnamed(db, story)
    except Exception:
        db.rollback()
    db.refresh(current)
    return current
