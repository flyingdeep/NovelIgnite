"""Blueprint baseline/living-state service."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.model_adapter import build_adapters, configured_model_specs, extract_json
from app.works.blueprint_schemas import BlueprintConfirm, BlueprintGenerationRequest, BlueprintUpdate
from app.works.concept_service import _model_for_config
from app.works.models import GenerationTask, StoryArtifact
from app.works.service import get_ai_config, get_story_or_404

BLUEPRINT_KINDS = ("characters", "world", "timeline", "arc")


def _json(artifact: StoryArtifact | None, fallback):
    return json.loads(artifact.payload) if artifact else fallback


def latest_blueprint(db: Session, story_id: str, kind: str) -> StoryArtifact | None:
    return db.scalar(select(StoryArtifact).where(StoryArtifact.story_id == story_id, StoryArtifact.kind == kind).order_by(StoryArtifact.version.desc()))


def list_blueprint(db: Session, story_id: str) -> dict[str, dict[str, Any] | None]:
    get_story_or_404(db, story_id)
    return {kind: latest_blueprint(db, story_id, kind) for kind in (*BLUEPRINT_KINDS, "living_state")}


def fallback_blueprint(idea: str, concept: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary = concept.get("summary") or idea
    return {
        "characters": {"title": "人物", "entries": [{"name": "主角", "role": "核心人物", "fields": {"background": "根据创意逐步确定", "motivation": "追查并解决核心冲突", "relationships": [], "constraints": "由作者确认"}}]},
        "world": {"title": "世界", "entries": [{"name": "故事世界", "role": "主要舞台", "fields": {"description": summary, "rules": [], "locations": [], "organizations": []}}]},
        "timeline": {"title": "初始时间线", "entries": [{"name": "故事开始", "role": "初始状态", "fields": {"before_story": [], "starting_state": summary, "known_unknowns": []}}]},
        "arc": {"title": "故事弧", "entries": [{"name": "主线冲突", "role": "全书方向", "fields": {"premise": summary, "phases": [], "turning_points": [], "ending_direction": "由作者确认"}}]},
    }


def normalize_blueprint_payload(payload: Any, idea: str, concept: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], bool]:
    if isinstance(payload, dict):
        source = payload.get("blueprint") if isinstance(payload.get("blueprint"), dict) else payload
        if all(isinstance(source.get(kind), dict) for kind in BLUEPRINT_KINDS):
            return source, False
        if isinstance(source.get("categories"), list):
            payload = source["categories"]
    if isinstance(payload, list):
        mapped: dict[str, dict[str, Any]] = {}
        aliases = {"character": "characters", "characters": "characters", "people": "characters", "world": "world", "setting": "world", "timeline": "timeline", "history": "timeline", "arc": "arc", "story_arc": "arc"}
        for item in payload:
            if not isinstance(item, dict):
                continue
            key = aliases.get(str(item.get("kind", item.get("type", ""))).lower())
            if key:
                mapped[key] = item
        if all(kind in mapped for kind in BLUEPRINT_KINDS):
            return mapped, False
    return fallback_blueprint(idea, concept), True


def generate_blueprint(db: Session, story_id: str, request: BlueprintGenerationRequest) -> list[StoryArtifact]:
    story = get_story_or_404(db, story_id)
    if story.stage not in {"concept_confirmed", "blueprint_review", "blueprint_confirmed"}:
        raise HTTPException(status_code=409, detail="Concept must be confirmed before Blueprint generation")
    config = get_ai_config(db, story_id)
    spec = _model_for_config(request.model or config.model)
    concept = latest_blueprint(db, story_id, "concept")
    concept_payload = _json(concept, {})
    task = GenerationTask(story_id=story.id, action="generate_blueprint", target_type="story", model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False), input_ref=json.dumps({"story_id": story.id, "concept_version": concept.version if concept else None}, ensure_ascii=False), status="running")
    db.add(task)
    db.flush()
    messages = [
        {"role": "system", "content": "你是小说蓝图策划助手。只返回合法 JSON，顶层必须有 characters、world、timeline、arc 四个对象。每个对象包含 title 和 entries；每个 entry 包含 name、role、fields。"},
        {"role": "user", "content": f"根据已确认故事概念与作者创意生成全局 Blueprint。只生成稳定 Baseline，不生成章节状态。Concept：{json.dumps(concept_payload, ensure_ascii=False)} Idea：{story.idea_text}"},
    ]
    try:
        adapter = build_adapters().get(spec.provider)
        if adapter:
            raw_payload = extract_json(adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=True, max_tokens=8192))
            payload, fallback_used = normalize_blueprint_payload(raw_payload, story.idea_text, concept_payload)
        else:
            payload = fallback_blueprint(story.idea_text, concept_payload)
            fallback_used = True
        artifacts = []
        for kind in BLUEPRINT_KINDS:
            previous = latest_blueprint(db, story.id, kind)
            artifact = StoryArtifact(story_id=story.id, kind=kind, layer="baseline", payload=json.dumps(payload.get(kind, {}), ensure_ascii=False), status="candidate", version=previous.version + 1 if previous else 1, locked_paths=json.dumps(json.loads(previous.locked_paths) if previous else [], ensure_ascii=False), source_task_id=task.id)
            db.add(artifact)
            db.flush()
            artifacts.append(artifact)
        task.status = "succeeded"
        task.target_id = artifacts[0].id
        task.output_summary = json.dumps({"kinds": list(BLUEPRINT_KINDS), "fallback_used": fallback_used}, ensure_ascii=False)
        story.stage = "blueprint_review"
        story.version += 1
        db.commit()
        for artifact in artifacts:
            db.refresh(artifact)
        return artifacts
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
        db.commit()
        raise HTTPException(status_code=502, detail="Blueprint generation failed; Concept remains unchanged") from exc


def update_blueprint(db: Session, story_id: str, kind: str, data: BlueprintUpdate) -> StoryArtifact:
    get_story_or_404(db, story_id)
    if kind not in BLUEPRINT_KINDS:
        raise HTTPException(status_code=404, detail="Blueprint kind not found")
    current = latest_blueprint(db, story_id, kind)
    if current is None:
        raise HTTPException(status_code=404, detail="Blueprint artifact not found")
    if current.status == "confirmed":
        raise HTTPException(status_code=409, detail="Confirmed Blueprint cannot be edited directly")
    if current.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Blueprint version conflict")
    previous_payload = json.loads(current.payload)
    locked = set(json.loads(current.locked_paths))
    for path in locked:
        if data.payload.get(path) != previous_payload.get(path):
            raise HTTPException(status_code=409, detail=f"Locked Blueprint field cannot be changed: {path}")
    artifact = StoryArtifact(story_id=story_id, kind=kind, layer="baseline", payload=json.dumps(data.payload, ensure_ascii=False), status="candidate", version=current.version + 1, locked_paths=json.dumps(sorted(locked | set(data.locked_paths)), ensure_ascii=False))
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def confirm_blueprint(db: Session, story_id: str, data: BlueprintConfirm) -> list[StoryArtifact]:
    story = get_story_or_404(db, story_id)
    artifacts = [latest_blueprint(db, story_id, kind) for kind in BLUEPRINT_KINDS]
    if any(artifact is None for artifact in artifacts):
        raise HTTPException(status_code=409, detail="All Blueprint categories must be generated first")
    if any(artifact.status == "confirmed" for artifact in artifacts):
        raise HTTPException(status_code=409, detail="Blueprint is already confirmed")
    for artifact in artifacts:
        expected = data.expected_versions.get(artifact.kind)
        if expected is not None and artifact.version != expected:
            raise HTTPException(status_code=409, detail=f"Blueprint version conflict: {artifact.kind}")
        artifact.status = "confirmed"
    living = latest_blueprint(db, story_id, "living_state")
    if living is None:
        living_payload = {
            "source": "initial_story_state",
            "temporal_scope": "story_start",
            "certainty": "confirmed",
            "context_policy": "always",
            "domains": {
                kind: {"source_ref": artifact.id, "version": artifact.version, "state": json.loads(artifact.payload)}
                for kind, artifact in zip(BLUEPRINT_KINDS, artifacts)
            },
        }
        living = StoryArtifact(
            story_id=story_id,
            kind="living_state",
            layer="living",
            payload=json.dumps(living_payload, ensure_ascii=False),
            status="confirmed",
            version=1,
            locked_paths="[]",
        )
        db.add(living)
    story.stage = "blueprint_confirmed"
    story.version += 1
    db.commit()
    for artifact in artifacts:
        db.refresh(artifact)
    return artifacts
