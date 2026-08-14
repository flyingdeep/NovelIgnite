"""Phase 5 Chapter Workspace service: snapshots, events, scenes, beats.

Provides:
- State Snapshot construction from confirmed Living State (no future info).
- Chapter Context assembly (snapshot + events + scenes + beats).
- Chapter Event editing (planned_result vs actual_result).
- Scene / Beat plan management with strict ordinal ordering.
- AI-generated Scene / Beat plan candidates (fallback to deterministic plans).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.model_adapter import build_adapters, extract_json
from app.infrastructure.prompts import prompt_version, system_prompt
from app.planning.models import Beat, Chapter, ChapterEvent, Scene, StateSnapshot
from app.planning.workspace_schemas import (
    BeatUpdate,
    ChapterEventUpdate,
    ScenePlanGenerationRequest,
    SceneUpdate,
)
from app.works.blueprint_service import latest_blueprint
from app.works.concept_service import _model_for_config
from app.works.models import GenerationTask
from app.planning.service import get_chapter
from app.works.service import get_ai_config, get_story_or_404

# Scene/Beat lifecycle (Phase 6 expands to generating/generated/applied/completed).
SCENE_STATUSES = ("planned", "available", "generating", "generated", "applied", "completed")
BEAT_STATUSES = ("planned", "available", "generating", "generated", "applied", "completed")

_FINISHED = {"completed", "applied"}


# ---------------------------------------------------------------------------
# Response serializers
# ---------------------------------------------------------------------------

def snapshot_response(snapshot: StateSnapshot | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    return {
        "chapter_id": snapshot.chapter_id,
        "based_on_chapter_id": snapshot.based_on_chapter_id,
        "state": json.loads(snapshot.state),
        "state_hash": snapshot.state_hash,
        "status": snapshot.status,
    }


def event_response(event: ChapterEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "chapter_id": event.chapter_id,
        "ordinal": event.ordinal,
        "title": event.title,
        "related_characters": json.loads(event.related_characters),
        "related_locations": json.loads(event.related_locations),
        "goal": event.goal,
        "planned_result": event.planned_result,
        "actual_result": event.actual_result,
        "impact": event.impact,
        "arc_role": event.arc_role,
        "version": event.version,
    }


def beat_response(beat: Beat, prose: dict[str, Any] | None = None) -> dict[str, Any]:
    data = {
        "id": beat.id,
        "scene_id": beat.scene_id,
        "ordinal": beat.ordinal,
        "name": beat.name,
        "instruction": beat.instruction,
        "status": beat.status,
        "version": beat.version,
    }
    if prose is not None:
        data["latest_prose"] = prose
    return data


def scene_response(scene: Scene, beats: list[Beat] | None = None) -> dict[str, Any]:
    data = {
        "id": scene.id,
        "chapter_id": scene.chapter_id,
        "ordinal": scene.ordinal,
        "title": scene.title,
        "location": scene.location,
        "time": scene.time,
        "pov": scene.pov,
        "character_goals": scene.character_goals,
        "conflict": scene.conflict,
        "key_events": scene.key_events,
        "scene_result": scene.scene_result,
        "chapter_goal_relation": scene.chapter_goal_relation,
        "summary": scene.summary,
        "status": scene.status,
        "version": scene.version,
    }
    if beats is not None:
        data["beats"] = [beat_response(b) for b in beats]
    return data


# ---------------------------------------------------------------------------
# State Snapshot
# ---------------------------------------------------------------------------

def build_state_snapshot(db: Session, story_id: str, chapter: Chapter) -> StateSnapshot:
    """Create (or refresh) the entering-state snapshot for a chapter."""
    living = latest_blueprint(db, story_id, "living_state")
    domains: dict[str, Any] = {}
    if living is not None:
        payload = json.loads(living.payload)
        living_domains = payload.get("domains") or {}
        for kind in ("characters", "world", "timeline"):
            domains[kind] = (living_domains.get(kind) or {}).get("state") or {}
    state = {"characters": domains.get("characters", {}), "world": domains.get("world", {}), "timeline": domains.get("timeline", {})}
    state_hash = hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    existing = db.scalar(select(StateSnapshot).where(StateSnapshot.chapter_id == chapter.id))
    if existing is not None:
        existing.state = json.dumps(state, ensure_ascii=False)
        existing.state_hash = state_hash
        existing.status = "valid"
        db.commit()
        db.refresh(existing)
        return existing
    snapshot = StateSnapshot(chapter_id=chapter.id, based_on_chapter_id=None, state=json.dumps(state, ensure_ascii=False), state_hash=state_hash, status="valid")
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


# ---------------------------------------------------------------------------
# Chapter Context
# ---------------------------------------------------------------------------

def get_chapter_context(db: Session, story_id: str, chapter_id: str) -> dict[str, Any]:
    story = get_story_or_404(db, story_id)
    chapter = get_chapter(db, story_id, chapter_id)
    snapshot = db.scalar(select(StateSnapshot).where(StateSnapshot.chapter_id == chapter.id))
    if snapshot is None or snapshot.status == "stale":
        snapshot = build_state_snapshot(db, story_id, chapter)
    events = list(db.scalars(select(ChapterEvent).where(ChapterEvent.chapter_id == chapter.id).order_by(ChapterEvent.ordinal)))
    scenes = list(db.scalars(select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.ordinal)))
    scene_responses = []
    for scene in scenes:
        beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
        beat_responses = []
        for beat in beats:
            from app.planning.models import ProseVersion
            prose = db.scalar(select(ProseVersion).where(ProseVersion.beat_id == beat.id).order_by(ProseVersion.version.desc()))
            beat_responses.append(beat_response(beat, prose={"version": prose.version, "status": prose.status, "markdown": prose.markdown, "applied_by": prose.applied_by} if prose else None))
        scene_data = scene_response(scene)
        scene_data["beats"] = beat_responses
        scene_responses.append(scene_data)
    return {
        "chapter": {
            "id": chapter.id,
            "ordinal": chapter.ordinal,
            "title": chapter.title,
            "goal": chapter.goal,
            "summary": chapter.summary,
            "access_status": chapter.access_status,
            "plan_status": chapter.plan_status,
            "version": chapter.version,
        },
        "snapshot": snapshot_response(snapshot),
        "events": [event_response(e) for e in events],
        "scenes": scene_responses,
    }


def get_story_reader(db: Session, story_id: str) -> dict[str, Any]:
    """Assemble the full reading-mode payload for a story.

    Returns every chapter (oldest first) with its scenes, and each scene's beats
    carrying the latest applied prose. The frontend renders a continuous novel:
    left = chapter list, right = content, Scene acts as a "节" navigation anchor.
    Only applied prose is included; planned content is excluded.
    """
    from app.planning.service import list_chapters
    from app.planning.models import ProseVersion

    story = get_story_or_404(db, story_id)
    chapters = list_chapters(db, story_id)
    chapter_data = []
    for chapter in chapters:
        scenes = list(db.scalars(select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.ordinal)))
        scene_data = []
        for scene in scenes:
            beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
            beat_paras = []
            for beat in beats:
                prose = db.scalar(select(ProseVersion).where(ProseVersion.beat_id == beat.id, ProseVersion.status == "applied").order_by(ProseVersion.version.desc()))
                if prose is None:
                    continue
                beat_paras.append({"beat_name": beat.name or f"Beat {beat.ordinal}", "markdown": prose.markdown})
            scene_data.append({"id": scene.id, "ordinal": scene.ordinal, "title": scene.title, "location": scene.location, "time": scene.time, "summary": scene.summary, "beats": beat_paras})
        chapter_data.append({
            "id": chapter.id,
            "ordinal": chapter.ordinal,
            "title": chapter.title,
            "goal": chapter.goal,
            "summary": chapter.summary,
            "access_status": chapter.access_status,
            "scenes": scene_data,
        })
    return {
        "story": {"id": story.id, "title": story.title, "stage": story.stage},
        "chapters": chapter_data,
    }


# ---------------------------------------------------------------------------
# Chapter Events
# ---------------------------------------------------------------------------

def get_event(db: Session, chapter_id: str, event_id: str) -> ChapterEvent:
    event = db.scalar(select(ChapterEvent).where(ChapterEvent.id == event_id, ChapterEvent.chapter_id == chapter_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Chapter Event not found")
    return event


def create_event(db: Session, story_id: str, chapter_id: str, title: str = "") -> ChapterEvent:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    existing = list(db.scalars(select(ChapterEvent).where(ChapterEvent.chapter_id == chapter.id).order_by(ChapterEvent.ordinal)))
    ordinal = (existing[-1].ordinal + 1) if existing else 1
    event = ChapterEvent(chapter_id=chapter.id, ordinal=ordinal, title=title)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, story_id: str, chapter_id: str, event_id: str, data: ChapterEventUpdate) -> ChapterEvent:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    event = get_event(db, chapter.id, event_id)
    if event.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Chapter Event version conflict")
    for field in ("title", "goal", "planned_result", "actual_result", "impact", "arc_role"):
        value = getattr(data, field)
        if value is not None:
            setattr(event, field, value)
    if data.related_characters is not None:
        event.related_characters = json.dumps(data.related_characters, ensure_ascii=False)
    if data.related_locations is not None:
        event.related_locations = json.dumps(data.related_locations, ensure_ascii=False)
    event.version += 1
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, story_id: str, chapter_id: str, event_id: str) -> None:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    event = get_event(db, chapter.id, event_id)
    db.delete(event)
    db.commit()


# ---------------------------------------------------------------------------
# Scenes & Beats
# ---------------------------------------------------------------------------

def get_scene(db: Session, chapter_id: str, scene_id: str) -> Scene:
    scene = db.scalar(select(Scene).where(Scene.id == scene_id, Scene.chapter_id == chapter_id))
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


def get_beat(db: Session, scene_id: str, beat_id: str) -> Beat:
    beat = db.scalar(select(Beat).where(Beat.id == beat_id, Beat.scene_id == scene_id))
    if beat is None:
        raise HTTPException(status_code=404, detail="Beat not found")
    return beat


def _require_active_chapter(db: Session, story_id: str, chapter_id: str) -> Chapter:
    story = get_story_or_404(db, story_id)
    chapter = get_chapter(db, story_id, chapter_id)
    if chapter.access_status != "active":
        raise HTTPException(status_code=409, detail="Locked Chapter cannot be edited")
    return chapter


def create_scene(db: Session, story_id: str, chapter_id: str, title: str = "") -> Scene:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    existing = list(db.scalars(select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.ordinal)))
    ordinal = (existing[-1].ordinal + 1) if existing else 1
    scene = Scene(chapter_id=chapter.id, ordinal=ordinal, title=title)
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


def update_scene(db: Session, story_id: str, chapter_id: str, scene_id: str, data: SceneUpdate) -> Scene:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    if scene.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Scene version conflict")
    for field in ("title", "location", "time", "pov", "character_goals", "conflict", "key_events", "scene_result", "chapter_goal_relation", "status"):
        value = getattr(data, field)
        if value is not None:
            if field == "status" and value not in SCENE_STATUSES:
                raise HTTPException(status_code=422, detail=f"Invalid scene status: {value}")
            setattr(scene, field, value)
    scene.version += 1
    db.commit()
    db.refresh(scene)
    return scene


def delete_scene(db: Session, story_id: str, chapter_id: str, scene_id: str) -> None:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    for beat in db.scalars(select(Beat).where(Beat.scene_id == scene.id)):
        db.delete(beat)
    db.delete(scene)
    db.commit()


def create_beat(db: Session, story_id: str, chapter_id: str, scene_id: str, name: str = "") -> Beat:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    existing = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
    ordinal = (existing[-1].ordinal + 1) if existing else 1
    beat = Beat(scene_id=scene.id, ordinal=ordinal, name=name)
    db.add(beat)
    db.commit()
    db.refresh(beat)
    return beat


def update_beat(db: Session, story_id: str, chapter_id: str, scene_id: str, beat_id: str, data: BeatUpdate) -> Beat:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    beat = get_beat(db, scene.id, beat_id)
    if beat.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Beat version conflict")
    if data.name is not None:
        beat.name = data.name
    if data.instruction is not None:
        beat.instruction = data.instruction
    if data.status is not None:
        if data.status not in BEAT_STATUSES:
            raise HTTPException(status_code=422, detail=f"Invalid beat status: {data.status}")
        beat.status = data.status
    beat.version += 1
    db.commit()
    db.refresh(beat)
    return beat


def delete_beat(db: Session, story_id: str, chapter_id: str, scene_id: str, beat_id: str) -> None:
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    beat = get_beat(db, scene.id, beat_id)
    db.delete(beat)
    db.commit()


# ---------------------------------------------------------------------------
# AI plan generation
# ---------------------------------------------------------------------------

def _fallback_scene_plan(chapter: Chapter, idea: str) -> list[dict[str, Any]]:
    seed = (idea or chapter.summary or "本章").strip()[:80]
    return [
        {"title": "开场", "location": "", "time": "", "pov": "", "character_goals": f"建立「{seed}」的入口，引入主角处境。", "conflict": "表层矛盾出现，主角被迫采取行动。", "key_events": "主角进入场景并接触核心冲突。", "scene_result": "主角获得第一条关键信息。", "chapter_goal_relation": chapter.goal or "推动本章目标"},
        {"title": "推进", "location": "", "time": "", "pov": "", "character_goals": "主角尝试解决问题。", "conflict": "阻力升级，暴露隐藏势力。", "key_events": "主角与关键人物交锋。", "scene_result": "主角获取线索并调整计划。", "chapter_goal_relation": chapter.goal or "深化本章目标"},
        {"title": "转折", "location": "", "time": "", "pov": "", "character_goals": "主角面对抉择。", "conflict": "代价显现，矛盾激化。", "key_events": "重要真相或伏笔被揭示。", "scene_result": "主角做出决定，为下一章铺垫。", "chapter_goal_relation": chapter.goal or "收束本章目标"},
    ]


def _fallback_beat_plan(scene: Scene) -> list[dict[str, Any]]:
    return [
        {"name": "场景进入", "instruction": "描写场景进入与环境，建立空间与情绪基调。"},
        {"name": "人物行动", "instruction": "主角采取行动，推进冲突。"},
        {"name": "冲突升级", "instruction": "阻力显现，冲突激化。"},
        {"name": "信息揭示", "instruction": "揭示关键信息或伏笔。"},
        {"name": "场景收束", "instruction": "收束场景，留下悬念或指向下一场景。"},
    ]


def _apply_scene_plan(db: Session, chapter: Chapter, scenes_data: list[dict[str, Any]]) -> list[Scene]:
    for old in db.scalars(select(Scene).where(Scene.chapter_id == chapter.id)):
        for beat in db.scalars(select(Beat).where(Beat.scene_id == old.id)):
            db.delete(beat)
        db.delete(old)
    db.flush()
    created = []
    for ordinal, item in enumerate(scenes_data, 1):
        scene = Scene(
            chapter_id=chapter.id,
            ordinal=ordinal,
            title=str(item.get("title") or f"Scene {ordinal}"),
            location=str(item.get("location") or ""),
            time=str(item.get("time") or ""),
            pov=str(item.get("pov") or ""),
            character_goals=str(item.get("character_goals") or ""),
            conflict=str(item.get("conflict") or ""),
            key_events=str(item.get("key_events") or ""),
            scene_result=str(item.get("scene_result") or ""),
            chapter_goal_relation=str(item.get("chapter_goal_relation") or ""),
            status="available" if ordinal == 1 else "planned",
        )
        db.add(scene)
        created.append(scene)
    db.flush()
    for scene in created:
        for b_ordinal, beat in enumerate(_fallback_beat_plan(scene), 1):
            db.add(Beat(scene_id=scene.id, ordinal=b_ordinal, name=beat["name"], instruction=beat["instruction"], status="available" if (scene.ordinal == 1 and b_ordinal == 1) else "planned"))
    return created


def generate_scene_plan(db: Session, story_id: str, chapter_id: str, request: ScenePlanGenerationRequest) -> list[Scene]:
    story = get_story_or_404(db, story_id)
    chapter = _require_active_chapter(db, story_id, chapter_id)
    config = get_ai_config(db, story_id)
    spec = _model_for_config(request.model or config.model)
    task = GenerationTask(story_id=story.id, action=request.action, target_type="chapter", target_id=chapter.id, model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False), prompt_version=prompt_version(request.action), input_ref=json.dumps({"chapter_id": chapter.id, "goal": chapter.goal}, ensure_ascii=False), status="running")
    db.add(task)
    db.flush()
    try:
        adapter = build_adapters().get(spec.provider)
        if adapter and request.action == "generate_scene_plan":
            messages = [
                {"role": "system", "content": system_prompt("generate_scene_plan")},
                {"role": "user", "content": f"根据章节计划生成场景计划。章节目标：{chapter.goal}。创意：{story.idea_text}"},
            ]
            raw = adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=True, action="generate_scene_plan")
            payload = extract_json(raw)
            if isinstance(payload, dict):
                for key in ("scenes", "plan", "items"):
                    if isinstance(payload.get(key), list):
                        payload = payload[key]
                        break
            scenes_data = payload if isinstance(payload, list) and payload else _fallback_scene_plan(chapter, story.idea_text)
        else:
            scenes_data = _fallback_scene_plan(chapter, story.idea_text)
        created = _apply_scene_plan(db, chapter, scenes_data)
        task.status = "succeeded"
        task.output_summary = json.dumps({"scene_count": len(created)}, ensure_ascii=False)
        db.commit()
        for scene in created:
            db.refresh(scene)
        return created
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
        db.commit()
        raise HTTPException(status_code=502, detail="Scene Plan generation failed; chapter plan unchanged") from exc


def generate_beat_plan(db: Session, story_id: str, chapter_id: str, scene_id: str, request: ScenePlanGenerationRequest) -> list[Beat]:
    story = get_story_or_404(db, story_id)
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    config = get_ai_config(db, story_id)
    spec = _model_for_config(request.model or config.model)
    task = GenerationTask(story_id=story.id, action=request.action, target_type="scene", target_id=scene.id, model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False), prompt_version=prompt_version(request.action), input_ref=json.dumps({"scene_id": scene.id, "title": scene.title}, ensure_ascii=False), status="running")
    db.add(task)
    db.flush()
    try:
        adapter = build_adapters().get(spec.provider)
        beats_data: list[dict[str, Any]]
        if adapter and request.action == "generate_beat_plan":
            messages = [
                {"role": "system", "content": system_prompt("generate_beat_plan")},
                {"role": "user", "content": f"根据场景计划生成节拍计划。场景：{scene.title}。场景目标：{scene.character_goals}。冲突：{scene.conflict}"},
            ]
            raw = adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=True, action="generate_beat_plan")
            payload = extract_json(raw)
            if isinstance(payload, dict):
                for key in ("beats", "plan", "items"):
                    if isinstance(payload.get(key), list):
                        payload = payload[key]
                        break
            beats_data = payload if isinstance(payload, list) and payload else _fallback_beat_plan(scene)
        else:
            beats_data = _fallback_beat_plan(scene)
        for old in db.scalars(select(Beat).where(Beat.scene_id == scene.id)):
            db.delete(old)
        db.flush()
        created = []
        for ordinal, item in enumerate(beats_data, 1):
            beat = Beat(scene_id=scene.id, ordinal=ordinal, name=str(item.get("name") or f"Beat {ordinal}"), instruction=str(item.get("instruction") or ""), status="available" if ordinal == 1 else "planned")
            db.add(beat)
            created.append(beat)
        task.status = "succeeded"
        task.output_summary = json.dumps({"beat_count": len(created)}, ensure_ascii=False)
        db.commit()
        for beat in created:
            db.refresh(beat)
        return created
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
        db.commit()
        raise HTTPException(status_code=502, detail="Beat Plan generation failed; scene plan unchanged") from exc
