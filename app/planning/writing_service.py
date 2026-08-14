"""Phase 6 writing service: prose versions, sequential generation, deltas, consistency.

Provides:
- Append-only Markdown prose versions per beat (candidate / applied).
- Sequential generation executor: generate one beat, a whole scene, or the rest of a chapter.
- Beat/Scene/Chapter checkpoints: proposed Delta extraction + consistency check.
- Chapter Delta merge and author confirmation (updates Living State, activates next chapter).
- Stale marking for later chapters when a historical chapter changes.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.model_adapter import build_adapters, extract_json
from app.planning.models import Beat, Chapter, ChapterEvent, ConsistencyIssue, ProseVersion, Scene, StateDelta, StateSnapshot
from app.planning.workspace_schemas import ProseVersionCreate, ScenePlanGenerationRequest
from app.planning.workspace_service import _require_active_chapter, get_beat, get_scene
from app.works.concept_service import _model_for_config
from app.works.models import GenerationTask, StoryArtifact
from app.works.service import get_ai_config

FINISHED_BEAT_STATUSES = {"applied", "completed"}


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def prose_response(pv: ProseVersion) -> dict[str, Any]:
    return {
        "id": pv.id,
        "story_id": pv.story_id,
        "chapter_id": pv.chapter_id,
        "scene_id": pv.scene_id,
        "beat_id": pv.beat_id,
        "markdown": pv.markdown,
        "parent_id": pv.parent_id,
        "version": pv.version,
        "status": pv.status,
        "applied_by": pv.applied_by,
    }


def delta_response(delta: StateDelta) -> dict[str, Any]:
    return {
        "id": delta.id,
        "story_id": delta.story_id,
        "chapter_id": delta.chapter_id,
        "scope_type": delta.scope_type,
        "scope_id": delta.scope_id,
        "source_version_id": delta.source_version_id,
        "changes": json.loads(delta.changes),
        "status": delta.status,
        "check_result": json.loads(delta.check_result),
    }


def issue_response(issue: ConsistencyIssue) -> dict[str, Any]:
    return {
        "id": issue.id,
        "story_id": issue.story_id,
        "chapter_id": issue.chapter_id,
        "checkpoint": issue.checkpoint,
        "scope_id": issue.scope_id,
        "rule": issue.rule,
        "severity": issue.severity,
        "evidence": issue.evidence,
        "status": issue.status,
    }


# ---------------------------------------------------------------------------
# Prose versions
# ---------------------------------------------------------------------------

def latest_prose(db: Session, beat_id: str) -> ProseVersion | None:
    return db.scalar(select(ProseVersion).where(ProseVersion.beat_id == beat_id).order_by(ProseVersion.version.desc()))


def list_prose(db: Session, beat_id: str) -> list[ProseVersion]:
    return list(db.scalars(select(ProseVersion).where(ProseVersion.beat_id == beat_id).order_by(ProseVersion.version)))


def apply_beat_prose(db: Session, story_id: str, chapter_id: str, scene_id: str, beat_id: str, data: ProseVersionCreate) -> ProseVersion:
    """Append an applied prose version for a beat (append-only; never overwrites history)."""
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    beat = get_beat(db, scene.id, beat_id)
    if beat.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Beat version conflict")
    prior = latest_prose(db, beat.id)
    version = (prior.version + 1) if prior else 1
    pv = ProseVersion(
        story_id=story_id,
        chapter_id=chapter.id,
        scene_id=scene.id,
        beat_id=beat.id,
        markdown=data.markdown,
        parent_id=prior.id if prior else None,
        version=version,
        status="applied",
        applied_by=data.applied_by,
    )
    db.add(pv)
    beat.status = "applied"
    beat.version += 1
    db.flush()
    # Checkpoint: author-applied prose also produces a proposed beat delta + consistency check,
    # so confirming the chapter projects real state changes into the next Living State version.
    create_beat_delta(db, story_id, chapter, scene, beat, pv)
    run_consistency_check(db, story_id, chapter, scene, beat, pv, checkpoint="beat")
    db.commit()
    db.refresh(pv)
    _complete_scene_if_done(db, scene)
    return pv


# ---------------------------------------------------------------------------
# Context & generation helpers
# ---------------------------------------------------------------------------

def _build_generation_messages(chapter: Chapter, scene: Scene, beat: Beat, snapshot_state: dict[str, Any], prior_prose: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "你是小说正文写作助手。根据章节/场景/节拍计划与进入本章时的故事快照，写出符合要求的 Markdown 正文。只输出正文，不输出元信息。"},
        {"role": "user", "content": f"章节目标：{chapter.goal or ''}\n章节梗概：{chapter.summary or ''}\n当前场景：{scene.title or ''}（地点：{scene.location or ''} · 时间：{scene.time or ''} · POV：{scene.pov or ''}）\n场景目标：{scene.character_goals or ''}，冲突：{scene.conflict or ''}，关键事件：{scene.key_events or ''}，场景结果：{scene.scene_result or ''}\n当前节拍：{beat.name or ''}\n节拍指令：{beat.instruction or ''}\n\n故事快照（仅本章开始前已成立的事实）：{json.dumps(snapshot_state, ensure_ascii=False)[:2000]}\n\n前序正文（若存在）：\n{prior_prose[:3000]}"},
    ]


def _fallback_prose(beat: Beat, scene: Scene) -> str:
    seed = (beat.instruction or beat.name or "本段").strip()[:120]
    return f"（{beat.name or f'Beat {beat.ordinal}'}）{seed}"


def _record_task(db: Session, story_id: str, chapter: Chapter, scene: Scene | None, beat: Beat | None, action: str, config) -> GenerationTask:
    task = GenerationTask(
        story_id=story_id,
        action=action,
        target_type="beat" if beat else "scene" if scene else "chapter",
        target_id=(beat or scene or chapter).id,
        model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False),
        input_ref=json.dumps({"chapter_id": chapter.id, "scene_id": scene.id if scene else None, "beat_id": beat.id if beat else None}, ensure_ascii=False),
        status="running",
    )
    db.add(task)
    db.flush()
    return task


def _generate_beat(db: Session, story_id: str, chapter: Chapter, scene: Scene, beat: Beat, config, request: ScenePlanGenerationRequest) -> ProseVersion:
    """Generate prose for a single beat and auto-apply it (append-only version history).

    Generated prose becomes the applied author-facing text immediately (author-approved
    auto-accept); previous versions are always preserved for rollback/regeneration.
    """
    adapter = build_adapters().get(_model_for_config(request.model or config.model).provider)
    snapshot = db.scalar(select(StateSnapshot).where(StateSnapshot.chapter_id == chapter.id))
    snapshot_state = json.loads(snapshot.state) if snapshot else {}
    prior = latest_prose(db, beat.id)
    prior_text = prior.markdown if prior and prior.status == "applied" else ""
    task = _record_task(db, story_id, chapter, scene, beat, "generate_scene", config)
    try:
        if adapter:
            messages = _build_generation_messages(chapter, scene, beat, snapshot_state, prior_text)
            raw = adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=False, action="generate_scene")
            markdown = (raw or "").strip() or _fallback_prose(beat, scene)
        else:
            markdown = _fallback_prose(beat, scene)
        version = (latest_prose(db, beat.id).version + 1) if latest_prose(db, beat.id) else 1
        pv = ProseVersion(story_id=story_id, chapter_id=chapter.id, scene_id=scene.id, beat_id=beat.id, markdown=markdown, parent_id=latest_prose(db, beat.id).id if latest_prose(db, beat.id) else None, version=version, status="applied", applied_by="ai")
        db.add(pv)
        beat.status = "applied"
        beat.version += 1
        task.status = "succeeded"
        task.output_summary = json.dumps({"char_len": len(markdown), "prose_version": version}, ensure_ascii=False)
        db.flush()
        # Checkpoint: proposed delta + consistency check on the generated prose.
        create_beat_delta(db, story_id, chapter, scene, beat, pv)
        run_consistency_check(db, story_id, chapter, scene, beat, pv, checkpoint="beat")
        db.commit()
        db.refresh(pv)
        return pv
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
        db.commit()
        raise HTTPException(status_code=502, detail="Beat prose generation failed; no existing prose was overwritten") from exc


def _complete_scene_if_done(db: Session, scene: Scene) -> bool:
    beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id)))
    if beats and all(b.status in FINISHED_BEAT_STATUSES for b in beats):
        scene.status = "completed"
        db.commit()
        db.refresh(scene)
        return True
    return False


# ---------------------------------------------------------------------------
# Sequential generation executor
# ---------------------------------------------------------------------------

def generate_scene(db: Session, story_id: str, chapter_id: str, scene_id: str, request: ScenePlanGenerationRequest) -> list[ProseVersion]:
    """Generate prose for every unfinished beat in a scene, in ordinal order."""
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    config = get_ai_config(db, story_id)
    beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
    if not beats:
        raise HTTPException(status_code=409, detail="Scene has no beats; generate a beat plan first")
    produced = []
    for beat in beats:
        if beat.status in FINISHED_BEAT_STATUSES:
            continue
        pv = _generate_beat(db, story_id, chapter, scene, beat, config, request)
        produced.append(pv)
    _complete_scene_if_done(db, scene)
    return produced


def generate_chapter_remaining(db: Session, story_id: str, chapter_id: str, request: ScenePlanGenerationRequest) -> list[ProseVersion]:
    """Generate prose for the rest of the chapter, scene by scene, beat by beat."""
    chapter = _require_active_chapter(db, story_id, chapter_id)
    config = get_ai_config(db, story_id)
    scenes = list(db.scalars(select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.ordinal)))
    if not scenes:
        raise HTTPException(status_code=409, detail="Chapter has no scenes; generate a scene plan first")
    produced = []
    for scene in scenes:
        beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
        for beat in beats:
            if beat.status in FINISHED_BEAT_STATUSES:
                continue
            pv = _generate_beat(db, story_id, chapter, scene, beat, config, request)
            produced.append(pv)
        _complete_scene_if_done(db, scene)
    return produced


def regenerate_beat(db: Session, story_id: str, chapter_id: str, scene_id: str, beat_id: str, request: ScenePlanGenerationRequest) -> ProseVersion:
    """Regenerate a beat's prose; creates a new applied version (never overwrites history)."""
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    beat = get_beat(db, scene.id, beat_id)
    if beat.status not in ("generated", "applied", "available", "completed"):
        raise HTTPException(status_code=409, detail="Only a current or already-generated beat can be regenerated")
    config = get_ai_config(db, story_id)
    return _generate_beat(db, story_id, chapter, scene, beat, config, request)


def generate_single_beat(db: Session, story_id: str, chapter_id: str, scene_id: str, beat_id: str, request: ScenePlanGenerationRequest) -> ProseVersion:
    """Generate prose for ONE specific beat (auto-applied).

    Idempotent: a beat that is already applied/completed is skipped and its
    latest prose is returned, so callers can loop beat-by-beat safely.
    """
    chapter = _require_active_chapter(db, story_id, chapter_id)
    scene = get_scene(db, chapter.id, scene_id)
    beat = get_beat(db, scene.id, beat_id)
    if beat.status in FINISHED_BEAT_STATUSES:
        existing = latest_prose(db, beat.id)
        if existing is None:
            raise HTTPException(status_code=409, detail="Beat is finished but has no prose")
        return existing
    config = get_ai_config(db, story_id)
    return _generate_beat(db, story_id, chapter, scene, beat, config, request)


# ---------------------------------------------------------------------------
# Delta extraction & consistency checkpoints
# ---------------------------------------------------------------------------

def _build_changes_from_prose(beat: Beat, scene: Scene, markdown: str) -> dict[str, Any]:
    """Heuristic placeholder for delta extraction (AI extraction is wired when adapter available)."""
    return {
        "character_changes": [],
        "world_changes": [],
        "timeline_changes": [{"event": beat.name or f"Beat {beat.ordinal}", "scene": scene.title or "", "note": "由本节正文推进"}],
        "scene_summary": markdown[:200],
    }


def create_beat_delta(db: Session, story_id: str, chapter: Chapter, scene: Scene, beat: Beat, pv: ProseVersion) -> StateDelta:
    existing = db.scalar(select(StateDelta).where(StateDelta.scope_type == "beat", StateDelta.scope_id == beat.id))
    if existing is not None:
        return existing
    delta = StateDelta(story_id=story_id, chapter_id=chapter.id, scope_type="beat", scope_id=beat.id, source_version_id=pv.id, changes=json.dumps(_build_changes_from_prose(beat, scene, pv.markdown), ensure_ascii=False), status="proposed", check_result=json.dumps({"issues": []}, ensure_ascii=False))
    db.add(delta)
    db.commit()
    db.refresh(delta)
    return delta


def run_consistency_check(db: Session, story_id: str, chapter: Chapter, scene: Scene, beat: Beat, pv: ProseVersion, checkpoint: str = "beat") -> list[ConsistencyIssue]:
    """Run a lightweight deterministic consistency check on generated prose."""
    issues: list[ConsistencyIssue] = []
    markdown = pv.markdown
    # Deterministic heuristics (no external model required).
    if len(markdown) < 20:
        issues.append(ConsistencyIssue(story_id=story_id, chapter_id=chapter.id, checkpoint=checkpoint, scope_id=beat.id, rule="prose_too_short", severity="warning", evidence=f"正文仅 {len(markdown)} 字，可能未完整覆盖节拍。", status="open"))
    for hint in ("（待补充）", "TODO", "占位"):
        if hint in markdown:
            issues.append(ConsistencyIssue(story_id=story_id, chapter_id=chapter.id, checkpoint=checkpoint, scope_id=beat.id, rule="placeholder_content", severity="warning", evidence=f"正文包含占位标记「{hint}」。", status="open"))
    if issues:
        db.add_all(issues)
        db.commit()
        for issue in issues:
            db.refresh(issue)
    return issues


def build_chapter_delta(db: Session, story_id: str, chapter: Chapter) -> StateDelta:
    """Merge beat/scene deltas into a chapter-level delta (proposed)."""
    existing = db.scalar(select(StateDelta).where(StateDelta.scope_type == "chapter", StateDelta.scope_id == chapter.id))
    if existing is not None:
        return existing
    beat_deltas = list(db.scalars(select(StateDelta).where(StateDelta.chapter_id == chapter.id, StateDelta.scope_type == "beat")))
    merged: dict[str, Any] = {"character_changes": [], "world_changes": [], "timeline_changes": []}
    for delta in beat_deltas:
        changes = json.loads(delta.changes)
        for key in merged:
            merged[key].extend(changes.get(key) or [])
    delta = StateDelta(story_id=story_id, chapter_id=chapter.id, scope_type="chapter", scope_id=chapter.id, source_version_id=None, changes=json.dumps(merged, ensure_ascii=False), status="proposed", check_result=json.dumps({"issues": []}, ensure_ascii=False))
    db.add(delta)
    db.commit()
    db.refresh(delta)
    return delta


# ---------------------------------------------------------------------------
# Chapter confirmation & next chapter activation
# ---------------------------------------------------------------------------

def _activate_next_chapter(db: Session, story: Any, chapter: Chapter) -> Chapter | None:
    next_chapter = db.scalar(select(Chapter).where(Chapter.story_id == chapter.story_id, Chapter.ordinal == chapter.ordinal + 1))
    if next_chapter is None:
        return None
    next_chapter.access_status = "active"
    next_chapter.plan_status = "fixed"
    return next_chapter


def _apply_changes_to_domains(domains: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """Project confirmed delta changes onto Living State domains.

    Immutable: returns a brand-new structure (deep copy) so earlier Living State
    versions stay intact for history tracing. character/world changes merge into
    existing named entries; timeline changes are appended as one chapter-scoped
    "事件推进" entry.
    """
    import copy

    new_domains = copy.deepcopy(domains or {})
    for domain_key, change_key in (("characters", "character_changes"), ("world", "world_changes")):
        state = dict(new_domains.get(domain_key, {}).get("state") or {})
        entries = list(state.get("entries") or [])
        for change in changes.get(change_key) or []:
            if not isinstance(change, dict) or not change.get("name"):
                continue
            fields = {k: v for k, v in (change.get("fields") or {}).items()}
            idx = next((i for i, e in enumerate(entries) if isinstance(e, dict) and e.get("name") == change["name"]), None)
            if idx is not None:
                merged = dict(entries[idx].get("fields") or {})
                merged.update(fields)
                entries[idx] = {**entries[idx], "fields": merged}
            else:
                entries.append({"name": change["name"], "fields": fields})
        state["entries"] = entries
        new_domains.setdefault(domain_key, {})["state"] = state
    timeline_changes = [c for c in (changes.get("timeline_changes") or []) if isinstance(c, dict) and c.get("event")]
    if timeline_changes:
        state = dict(new_domains.get("timeline", {}).get("state") or {})
        entries = list(state.get("entries") or [])
        entries.append(
            {
                "name": f"第 {changes.get('chapter_ordinal', '?')} 章 · 事件推进",
                "fields": {
                    "events": [
                        {"event": c.get("event"), "scene": c.get("scene", ""), "note": c.get("note", "")} for c in timeline_changes
                    ],
                    "note": "由已确认 Chapter Delta 追加",
                },
            }
        )
        state["entries"] = entries
        new_domains.setdefault("timeline", {})["state"] = state
    return new_domains


def confirm_chapter_delta(db: Session, story_id: str, chapter_id: str, expected_delta_id: str | None = None) -> dict[str, Any]:
    """Author confirms the chapter delta: finalize chapter, update story state, activate next chapter."""
    from app.planning.workspace_service import get_chapter_context
    from app.works.blueprint_service import latest_blueprint
    from app.works.service import get_story_or_404

    story = get_story_or_404(db, story_id)
    chapter = db.get(Chapter, chapter_id)
    if chapter is None or chapter.story_id != story_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    if chapter.access_status != "active":
        raise HTTPException(status_code=409, detail="Chapter is not active")
    # Integrity gate: every scene's every beat must have applied prose before a
    # chapter can be confirmed. This prevents "completed" chapters with missing
    # scenes (a historical bug where partial scenes were confirmed).
    scenes = list(db.scalars(select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.ordinal)))
    if not scenes:
        raise HTTPException(status_code=409, detail="Chapter has no scenes; generate a scene plan first")
    missing: list[str] = []
    for scene in scenes:
        beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
        for beat in beats:
            applied = db.scalar(select(ProseVersion).where(ProseVersion.beat_id == beat.id, ProseVersion.status == "applied"))
            if applied is None:
                missing.append(f"场景 {scene.ordinal}「{scene.title or ''}」Beat {beat.ordinal}「{beat.name or ''}」")
    if missing:
        detail = "；".join(missing[:10])
        raise HTTPException(status_code=409, detail=f"Chapter 尚未全部完成，不能确认 Delta：{detail}")
    delta = db.scalar(select(StateDelta).where(StateDelta.scope_type == "chapter", StateDelta.scope_id == chapter.id))
    if delta is None:
        delta = build_chapter_delta(db, story_id, chapter)
    if expected_delta_id and delta.id != expected_delta_id:
        raise HTTPException(status_code=409, detail="Chapter Delta version conflict")
    if delta.status != "confirmed":
        delta.status = "confirmed"
        db.add(delta)

    # Update Living State projection: create a NEW Living State version (v+1) that
    # applies this chapter's confirmed delta changes to the three domains. Earlier
    # versions are preserved as immutable history entries.
    living = latest_blueprint(db, story_id, "living_state")
    if living is not None:
        payload = json.loads(living.payload)
        changes = json.loads(delta.changes)
        changes["chapter_ordinal"] = chapter.ordinal
        new_payload = {
            "source": payload.get("source", "chapter_delta"),
            "temporal_scope": payload.get("temporal_scope", "story_progress"),
            "certainty": "confirmed",
            "context_policy": payload.get("context_policy", "always"),
            "domains": _apply_changes_to_domains(payload.get("domains") or {}, changes),
            "last_confirmed_chapter": chapter.ordinal,
            "confirmed_deltas": payload.get("confirmed_deltas", []) + [{"chapter_ordinal": chapter.ordinal, "delta_id": delta.id, "changes": json.loads(delta.changes)}],
        }
        db.add(StoryArtifact(story_id=story_id, kind="living_state", layer="living", payload=json.dumps(new_payload, ensure_ascii=False), status="confirmed", version=living.version + 1, locked_paths="[]"))

    chapter.access_status = "completed"
    chapter.plan_status = "fixed"
    db.add(chapter)
    next_chapter = _activate_next_chapter(db, story, chapter)
    all_chapters = list(db.scalars(select(Chapter).where(Chapter.story_id == story.id).order_by(Chapter.ordinal)))
    if all_chapters and all(c.access_status == "completed" for c in all_chapters):
        story.stage = "done"
        story.progress_text = "已完成"
    else:
        story.stage = "writing"
        story.progress_text = f"第 {next_chapter.ordinal if next_chapter else chapter.ordinal} 章 / {len(all_chapters)} 章" if next_chapter else f"第 {chapter.ordinal} 章 / {len(all_chapters)} 章"
    story.version += 1
    db.commit()

    context = get_chapter_context(db, story_id, chapter.id)
    result: dict[str, Any] = {"status": "confirmed", "delta": delta_response(delta), "chapter": context["chapter"]}
    if next_chapter is not None:
        db.refresh(next_chapter)
        result["next_chapter"] = {"id": next_chapter.id, "ordinal": next_chapter.ordinal, "title": next_chapter.title, "access_status": next_chapter.access_status}
    return result


# ---------------------------------------------------------------------------
# Stale marking & recompute
# ---------------------------------------------------------------------------

def mark_subsequent_stale(db: Session, story_id: str, changed_ordinal: int) -> int:
    """Mark snapshots of all chapters after the changed one as stale."""
    from app.works.service import get_story_or_404
    story = get_story_or_404(db, story_id)
    later = list(db.scalars(select(Chapter).where(Chapter.story_id == story.id, Chapter.ordinal > changed_ordinal).order_by(Chapter.ordinal)))
    count = 0
    for chapter in later:
        snapshot = db.scalar(select(StateSnapshot).where(StateSnapshot.chapter_id == chapter.id))
        if snapshot is not None:
            snapshot.status = "stale"
            count += 1
        chapter.stale_reason = f"Chapter {changed_ordinal} 内容变更，需按序重算"
    if count:
        db.commit()
    return count
