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
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.model_adapter import build_adapters, extract_json
from app.infrastructure.model_prompt_profiles import compose_system_prompt
from app.infrastructure.prompts import prompt_version, system_prompt
from app.planning.models import Beat, Chapter, ChapterEvent, ConsistencyIssue, ProseVersion, Scene, StateDelta, StateSnapshot
from app.planning.workspace_schemas import ProseVersionCreate, ScenePlanGenerationRequest
from app.planning.workspace_service import _require_active_chapter, get_beat, get_scene
from app.works.blueprint_service import BLUEPRINT_KINDS, build_blueprint_context, build_focused_blueprint_context, latest_blueprint
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
    config = get_ai_config(db, story_id)
    create_beat_delta(db, story_id, chapter, scene, beat, pv, config)
    run_consistency_check(db, story_id, chapter, scene, beat, pv, checkpoint="beat", config=config)
    db.commit()
    db.refresh(pv)
    _complete_scene_if_done(db, scene, config)
    return pv


# ---------------------------------------------------------------------------
# Context & generation helpers
# ---------------------------------------------------------------------------

def _latest_prev_beat_prose(db: Session, scene: Scene, beat: Beat) -> str:
    """取紧邻当前 Beat 的上一个 Beat 的完整已应用正文（跨场景向前追溯）。"""
    prev = db.scalar(select(Beat).where(Beat.scene_id == scene.id, Beat.ordinal < beat.ordinal).order_by(Beat.ordinal.desc()))
    if prev is None:
        prev_scene = db.scalar(select(Scene).where(Scene.chapter_id == scene.chapter_id, Scene.ordinal < scene.ordinal).order_by(Scene.ordinal.desc()))
        if prev_scene is not None:
            prev = db.scalar(select(Beat).where(Beat.scene_id == prev_scene.id).order_by(Beat.ordinal.desc()))
    if prev is None:
        return ""
    pv = db.scalar(select(ProseVersion).where(ProseVersion.beat_id == prev.id, ProseVersion.status == "applied").order_by(ProseVersion.version.desc()))
    return pv.markdown if pv else ""


def build_story_progress_summary(db: Session, story_id: str) -> str:
    """全书至今的故事进展摘要（按章节/场景顺序汇总已完结场景的 summary）。

    供正文生成的「至今故事摘要」要素；仅统计已完成场景，过长时保留最近 6 条。
    """
    chapters = list(db.scalars(select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.ordinal)))
    blocks: list[str] = []
    for ch in chapters:
        scenes = list(db.scalars(select(Scene).where(Scene.chapter_id == ch.id).order_by(Scene.ordinal)))
        for sc in scenes:
            if sc.status == "completed" and sc.summary:
                blocks.append(f"第{ch.ordinal}章·场景{sc.ordinal}「{sc.title or ''}」：{sc.summary}")
    if not blocks:
        return ""
    if len(blocks) <= 6:
        return "\n".join(blocks)
    return f"（更早还有 {len(blocks) - 6} 个已完结场景，摘要略）\n" + "\n".join(blocks[-6:])


def _build_character_state_card(scene: Scene, snapshot_state: dict[str, Any]) -> str:
    """B·即时状态卡：从章节入口快照提取当前 POV 人物的即时状态，作为连贯锚点。

    让模型知道人物「此刻在哪里、在做什么、情绪如何、目标是什么」，避免上下文里
    只有密集设定而没有当前动作锚点；同时与上一 Beat 的衔接共同支撑连贯性。
    """
    pov = (scene.pov or "").strip()
    if not pov:
        return ""
    state = (snapshot_state or {}).get("characters") or {}
    entries = state.get("entries") if isinstance(state, dict) else []
    if not isinstance(entries, list):
        return ""
    entry = next((e for e in entries if isinstance(e, dict) and (e.get("name") or "") == pov), None)
    if not entry:
        return f"- 人物：{pov}（本章入口快照中暂无该人物即时明细，以蓝图设定为准）"
    fields = entry.get("fields")
    if isinstance(fields, str):
        return f"- 人物：{pov}\n- 快照：{fields[:300]}"
    if not isinstance(fields, dict):
        return f"- 人物：{pov}"
    keys = ("位置", "地点", "所在", "情绪", "心态", "目标", "行动", "状态", "身心", "关系", "掌握", "携带", "物品", "穿着", "着装", "动作", "决断", "意图")
    lines = [f"- 人物：{pov}"]
    for k, v in fields.items():
        if any(kk in str(k) for kk in keys):
            val = v if isinstance(v, str) else ("；".join(str(x) for x in v) if isinstance(v, list) else str(v))
            lines.append(f"- {k}：{val}")
    if len(lines) == 1:
        lines.append("- 本章入口快照中暂无即时状态明细")
    return "\n".join(lines)


def _build_generation_messages(db: Session, chapter: Chapter, scene: Scene, beat: Beat, snapshot_state: dict[str, Any], prior_prose: str) -> list[dict[str, str]]:
    # Revise later plans: include summaries of earlier completed scenes so the
    # current beat builds on what already happened (Scene Summary feature).
    earlier_scenes = list(db.scalars(select(Scene).where(Scene.chapter_id == chapter.id, Scene.ordinal < scene.ordinal).order_by(Scene.ordinal)))
    summaries = []
    for earlier in earlier_scenes:
        if earlier.summary:
            summaries.append(f"Scene {earlier.ordinal}「{earlier.title or ''}」：{earlier.summary}")
    prior_scenes_block = ("\n".join(summaries) + "\n\n") if summaries else ""
    prev_scene_summary = summaries[-1] if summaries else ""
    # A·聚焦蓝图（只注入当前 POV/地点的相关设定，减少设定密度对行文的挤压）：
    # 概念 + 全部人物（POV 置顶）+ 按当前地点过滤的世界 + 时间线/剧情弧。
    blueprint_ctx = build_focused_blueprint_context(db, chapter.story_id, pov=scene.pov or "", location=scene.location or "", max_chars=14000)
    model_provider = _model_for_config(get_ai_config(db, chapter.story_id).model).provider
    # B·即时状态卡 + 场景情绪走向（连贯锚点）
    state_card = _build_character_state_card(scene, snapshot_state)
    emotion_line = (f"本场景情绪走向：由冲突「{scene.conflict or ''}」驱动，围绕目标「{scene.character_goals or ''}」，向「{scene.scene_result or ''}」收束。"
                    f"写作时先把『谁在哪、在做什么』写清楚，再让读者的情绪沿这条线自然流动，不要直接堆氛围或设定。")
    # Beat 三要素：上一个 Beat 完整正文、上一个 Scene 摘要、全书进展摘要
    prev_beat_prose = _latest_prev_beat_prose(db, scene, beat)
    story_progress = build_story_progress_summary(db, chapter.story_id)
    return [
        {"role": "system", "content": compose_system_prompt(db, model_provider, "generate_scene")},
        {"role": "user", "content": (
            f"章节目标：{chapter.goal or ''}\n"
            f"章节梗概：{chapter.summary or ''}\n"
            f"当前场景：{scene.title or ''}（地点：{scene.location or ''} · 时间：{scene.time or ''} · POV：{scene.pov or ''}）\n"
            f"场景目标：{scene.character_goals or ''}，冲突：{scene.conflict or ''}，关键事件：{scene.key_events or ''}，场景结果：{scene.scene_result or ''}\n"
            f"当前节拍：{beat.name or ''}\n"
            f"节拍指令：{beat.instruction or ''}\n\n"
            f"权威故事蓝图（聚焦当前场景的 POV 与地点；任何章节/场景/节拍写作都必须以此为准，不得违背或自创冲突设定）：\n{blueprint_ctx}\n\n"
            f"当前 POV 人物即时状态（来自本章入口快照，保持连贯，不要写与快照矛盾的状态）：\n{state_card or '（无）'}\n\n"
            f"{emotion_line}\n\n"
            f"上一个 Beat 完整正文（紧邻衔接用）：\n{prev_beat_prose[:2500] or '（本段为开篇，无上一个 Beat）'}\n\n"
            f"上一个 Scene 摘要：\n{prev_scene_summary or '（本场景为本章首个场景，无上一个 Scene）'}\n\n"
            f"全书进展摘要（故事至此为止）：\n{story_progress[:1200] or '（故事刚开始，尚无进展）'}\n\n"
            f"故事快照（仅本章开始前已成立的事实）：{json.dumps(snapshot_state, ensure_ascii=False)[:4000]}\n\n"
            f"前序已发生场景摘要（保持剧情连贯）：\n{prior_scenes_block}"
            f"前序正文（若存在）：\n{prior_prose[:3000]}"
        )},
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
        prompt_version=prompt_version(action),
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
            messages = _build_generation_messages(db, chapter, scene, beat, snapshot_state, prior_text)
            raw = adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=False, action="generate_scene")
            markdown = (raw or "").strip() or _fallback_prose(beat, scene)
            # C·可读性自检：轻量重写（保持原意/情节/事实不变，只提升可读性与自然度）。
            # 失败或返回为空/原文时静默保持初稿，绝不阻塞写作。
            try:
                review_messages = [
                    {"role": "system", "content": compose_system_prompt(db, _model_for_config(config.model).provider, "readability_review")},
                    {"role": "user", "content": f"请检查并重写以下正文（保持原意、情节与人物言行完全不变，只提升可读性与自然度；若已通顺则原样返回）：\n\n{markdown}"},
                ]
                rewritten = adapter.complete(review_messages, temperature=0.3, reasoning_strength="low", json_mode=False, action="readability_review")
                rw = (rewritten or "").strip()
                if rw and rw != markdown:
                    markdown = rw
            except Exception:
                pass
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
        create_beat_delta(db, story_id, chapter, scene, beat, pv, config)
        run_consistency_check(db, story_id, chapter, scene, beat, pv, checkpoint="beat", config=config)
        # 独立 review 检查点：每个 Beat 都判断是否出现需要纳入全局蓝图的新设定。
        # 建议仍为 candidate，只有作者显式确认后才能改变 baseline。
        review_blueprint_updates(db, story_id, chapter, scene, beat, config, scope="beat")
        db.commit()
        db.refresh(pv)
        return pv
    except Exception as exc:
        task.status = "failed"
        task.error_type = type(exc).__name__
        db.commit()
        raise HTTPException(status_code=502, detail="Beat prose generation failed; no existing prose was overwritten") from exc


def _ai_scene_summary(db: Session, scene: Scene, config) -> str:
    """Generate an AI Scene Summary from the scene's applied prose.

    Falls back to the scene_result / first beat text when no model is available
    or the call fails. Never blocks generation.
    """
    beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
    prose_parts = []
    for beat in beats:
        pv = db.scalar(select(ProseVersion).where(ProseVersion.beat_id == beat.id, ProseVersion.status == "applied").order_by(ProseVersion.version.desc()))
        if pv and pv.markdown:
            prose_parts.append(pv.markdown)
    if not prose_parts:
        return scene.scene_result or ""
    joined = "\n\n".join(prose_parts)
    adapter = build_adapters().get(_model_for_config(config.model).provider)
    if adapter is None:
        return joined[:300]
    messages = [
        {"role": "system", "content": compose_system_prompt(db, _model_for_config(config.model).provider, "scene_summary")},
        {"role": "user", "content": f"场景：{scene.title or ''}（地点：{scene.location or ''} · 时间：{scene.time or ''} · POV：{scene.pov or ''}）\n场景目标：{scene.character_goals or ''}，结果：{scene.scene_result or ''}\n\n正文：\n{joined[:4000]}"},
    ]
    try:
        raw = adapter.complete(messages, temperature=0.3, reasoning_strength="low", json_mode=False, action="scene_summary")
        summary = (raw or "").strip()
        if not summary:
            raise ValueError("empty summary")
        return summary[:500]
    except Exception:
        return joined[:300]


def _complete_scene_if_done(db: Session, scene: Scene, config=None) -> bool:
    beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id)))
    if beats and all(b.status in FINISHED_BEAT_STATUSES for b in beats):
        scene.status = "completed"
        # Generate the Scene Summary once (only on first completion), then feed it
        # into the next scene's plan context so later scenes build on it.
        if config is not None and not scene.summary:
            try:
                scene.summary = _ai_scene_summary(db, scene, config)
            except Exception:
                scene.summary = scene.scene_result or ""
        # 独立 review 环节：判断本 Scene 产出是否需要更新蓝图（不阻塞，失败静默）
        if config is not None:
            try:
                ch = db.get(Chapter, scene.chapter_id)
                if ch is not None:
                    review_blueprint_updates(db, ch.story_id, ch, scene, None, config, scope="scene")
            except Exception:
                pass
        db.commit()
        db.refresh(scene)
        return True
    return False


def auto_apply_blueprint_updates(db: Session, story_id: str, suggestions: list[dict[str, Any]], *, chapter_ordinal: int | None = None, scope: str = "") -> dict[str, int]:
    """把 review 建议自动应用到对应 kind 的 baseline 蓝图（append-only，供「更新履历」追溯）。

    设计：用户要求蓝图更新活动自动触发并反映到各分类说明与更新履历，不再需要
    「待确认」长列表。为保留安全与可追溯性，自动应用遵循：
    - 跳过作者锁定（locked_paths 含 kind 或目标条目名）的建议；
    - 同一 kind 若最新版本已是「AI 自动应用」产物（payload 含 _ai_updates 标记）则就地合并，
      避免每个 Beat/Scene 都发新版本导致版本爆炸；否则创建 version+1 新版本（原版本保留）；
    - 每次应用追加到 payload["_ai_updates"] 供前端「更新履历」展示；该元数据键不会进入模型上下文。
    返回 {kind: 应用条数}。
    """
    import copy

    grouped: dict[str, list[dict[str, Any]]] = {}
    for s in suggestions:
        if not isinstance(s, dict):
            continue
        kind = str(s.get("kind") or "")
        if kind not in BLUEPRINT_KINDS:
            continue
        if s.get("action") not in ("add", "modify") or not str(s.get("target") or "").strip():
            continue
        grouped.setdefault(kind, []).append(s)

    applied: dict[str, int] = {}
    for kind, items in grouped.items():
        artifact = latest_blueprint(db, story_id, kind)
        if artifact is None:
            continue
        locked = set(json.loads(artifact.locked_paths) or [])
        payload = copy.deepcopy(json.loads(artifact.payload))
        entries = payload.setdefault("entries", [])
        count = 0
        for s in items:
            target = str(s.get("target") or "").strip()
            change = str(s.get("change") or "").strip() or target
            evidence = str(s.get("evidence") or "").strip()
            if kind in locked or target in locked:
                continue
            entry = next((e for e in entries if isinstance(e, dict) and e.get("name") == target), None)
            if entry is None:
                entry = {"name": target, "role": "AI 自动更新", "fields": {}}
                entries.append(entry)
            entry["fields"]["AI 自动更新"] = change
            if evidence:
                entry["fields"]["证据"] = evidence
            count += 1
        if not count:
            continue
        had_ai_updates = "_ai_updates" in payload
        updates = payload.setdefault("_ai_updates", [])
        updates.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "scope": scope,
            "chapter_ordinal": chapter_ordinal,
            "count": count,
            "items": [{"action": s.get("action"), "kind": kind, "target": str(s.get("target") or "")} for s in items],
        })
        if had_ai_updates:
            artifact.payload = json.dumps(payload, ensure_ascii=False)
        else:
            db.add(StoryArtifact(
                story_id=story_id,
                kind=kind,
                layer="baseline",
                payload=json.dumps(payload, ensure_ascii=False),
                status=artifact.status,
                version=artifact.version + 1,
                locked_paths=artifact.locked_paths,
                source_task_id=artifact.source_task_id,
            ))
        applied[kind] = count
    return applied


def review_blueprint_updates(db: Session, story_id: str, chapter: Chapter, scene: Scene | None, beat: Beat | None, config, *, scope: str) -> list[dict[str, Any]]:
    """产出后的蓝图更新 review：判断新产出是否引入需要更新 baseline 蓝图的新设定。

    scope: beat | scene | chapter。scene/chapter 级调模型产出建议，**自动应用**到对应
    分类 baseline（append-only 新版本 + 锁定字段保护 + 履历记录），并保留一条
    StoryArtifact(kind="blueprint_review", status="applied") 作审计。失败静默，绝不阻塞写作流程。
    """
    if scope not in ("beat", "scene", "chapter"):
        return []
    adapter = build_adapters().get(_model_for_config(config.model).provider)
    if adapter is None:
        return []
    prose_parts: list[str] = []
    if scope == "beat" and beat is not None:
        pv = latest_prose(db, beat.id)
        if pv:
            prose_parts.append(pv.markdown)
    elif scope == "scene" and scene is not None:
        for b in db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)):
            pv = latest_prose(db, b.id)
            if pv:
                prose_parts.append(pv.markdown)
    else:  # chapter
        for sc in db.scalars(select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.ordinal)):
            for b in db.scalars(select(Beat).where(Beat.scene_id == sc.id).order_by(Beat.ordinal)):
                pv = latest_prose(db, b.id)
                if pv:
                    prose_parts.append(pv.markdown)
    prose_text = "\n\n".join(prose_parts)[:6000]
    if not prose_text:
        return []
    blueprint_ctx = build_blueprint_context(db, story_id, max_chars=6000)
    messages = [
        {"role": "system", "content": compose_system_prompt(db, _model_for_config(config.model).provider, "review_blueprint_updates")},
        {"role": "user", "content": f"review 范围：{scope}（第{chapter.ordinal}章）\n\n当前权威蓝图：\n{blueprint_ctx}\n\n本单元已应用正文：\n{prose_text}"},
    ]
    try:
        raw = adapter.complete(messages, temperature=0.3, reasoning_strength="low", json_mode=True, action="review_blueprint_updates")
        suggestions = extract_json(raw)
        if not isinstance(suggestions, list):
            suggestions = []
        if suggestions:
            previous = db.scalar(select(StoryArtifact).where(StoryArtifact.story_id == story_id, StoryArtifact.kind == "blueprint_review").order_by(StoryArtifact.version.desc()))
            db.add(StoryArtifact(
                story_id=story_id,
                kind="blueprint_review",
                layer="living",
                payload=json.dumps({"scope": scope, "chapter_ordinal": chapter.ordinal, "scene_id": scene.id if scene else None, "beat_id": beat.id if beat else None, "suggestions": suggestions}, ensure_ascii=False),
                status="applied",
                version=(previous.version + 1 if previous else 1),
                source_task_id=None,
            ))
            db.flush()
            auto_apply_blueprint_updates(db, story_id, suggestions, chapter_ordinal=chapter.ordinal, scope=scope)
        return suggestions
    except Exception:
        return []


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
    _complete_scene_if_done(db, scene, config)
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
        _complete_scene_if_done(db, scene, config)
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
    pv = _generate_beat(db, story_id, chapter, scene, beat, config, request)
    # The workspace UI generates scenes beat-by-beat; finalize the scene (status +
    # Scene Summary) as soon as the last beat is applied.
    _complete_scene_if_done(db, scene, config)
    return pv


def backfill_missing_prose(db: Session, story_id: str, chapter_id: str, request: ScenePlanGenerationRequest) -> list[ProseVersion]:
    """Backfill missing beat prose in a (possibly completed) chapter.

    Generates prose for every beat that has no applied version yet, using the
    chapter's ENTRY snapshot as context (never later-chapter state), so the
    newly written prose stays consistent with what was known at that chapter's
    start. After writing, later chapters' snapshots are marked stale because a
    historical chapter's facts changed.
    """
    from app.planning.service import get_chapter
    from app.works.service import get_story_or_404

    story = get_story_or_404(db, story_id)
    chapter = get_chapter(db, story_id, chapter_id)
    if chapter.access_status not in ("active", "completed"):
        raise HTTPException(status_code=409, detail="Only active or completed chapters can be backfilled")
    config = get_ai_config(db, story_id)
    scenes = list(db.scalars(select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.ordinal)))
    produced: list[ProseVersion] = []
    for scene in scenes:
        beats = list(db.scalars(select(Beat).where(Beat.scene_id == scene.id).order_by(Beat.ordinal)))
        for beat in beats:
            if beat.status in FINISHED_BEAT_STATUSES:
                continue
            existing = latest_prose(db, beat.id)
            if existing is not None and existing.status == "applied":
                continue
            pv = _generate_beat(db, story_id, chapter, scene, beat, config, request)
            produced.append(pv)
        _complete_scene_if_done(db, scene)
    if produced:
        mark_subsequent_stale(db, story_id, chapter.ordinal)
        db.commit()
        for pv in produced:
            db.refresh(pv)
    return produced


# ---------------------------------------------------------------------------
# Delta extraction & consistency checkpoints
# ---------------------------------------------------------------------------

def _ai_extract_changes(db: Session, chapter: Chapter, scene: Scene, beat: Beat, markdown: str, snapshot_state: dict[str, Any], config) -> dict[str, Any] | None:
    """AI-driven delta extraction from generated prose.

    Asks the configured model to derive character/world/timeline state changes
    from the prose relative to the chapter-entry snapshot. Returns None on any
    failure (no adapter, missing key, non-JSON, etc.) so callers fall back to
    the deterministic heuristic — the prose is never lost.
    """
    adapter = build_adapters().get(_model_for_config(config.model).provider)
    if adapter is None:
        return None
    messages = [
        {"role": "system", "content": compose_system_prompt(db, _model_for_config(config.model).provider, "extract_delta")},
        {"role": "user", "content": f"章节开始快照：{json.dumps(snapshot_state, ensure_ascii=False)[:2500]}\n\n场景：{scene.title or ''}\n节拍：{beat.name or f'Beat {beat.ordinal}'}\n\n正文：\n{markdown[:4000]}"},
    ]
    try:
        raw = adapter.complete(messages, temperature=0.2, reasoning_strength="low", json_mode=True, action="extract_delta")
        payload = extract_json(raw)
        if not isinstance(payload, dict):
            return None
        changes = {
            "character_changes": payload.get("character_changes") or [],
            "world_changes": payload.get("world_changes") or [],
            "timeline_changes": payload.get("timeline_changes") or [],
        }
        # Normalize: ensure each change is a dict with a name.
        for key in ("character_changes", "world_changes", "timeline_changes"):
            cleaned = []
            for item in changes[key]:
                if isinstance(item, dict):
                    cleaned.append(item)
            changes[key] = cleaned
        return changes
    except Exception:
        return None


def _build_changes_from_prose(db: Session, chapter: Chapter, scene: Scene, beat: Beat, markdown: str, config) -> dict[str, Any]:
    """Delta extraction for a beat.

    Prefers AI-driven extraction (derive character/world/timeline changes from
    the prose); falls back to a deterministic heuristic when no model is
    available or the model call fails. The author's prose is never discarded.
    """
    snapshot = db.scalar(select(StateSnapshot).where(StateSnapshot.chapter_id == chapter.id))
    snapshot_state = json.loads(snapshot.state) if snapshot else {}
    ai = _ai_extract_changes(db, chapter, scene, beat, markdown, snapshot_state, config)
    if ai is not None:
        ai["scene_summary"] = markdown[:300]
        return ai
    return {
        "character_changes": [],
        "world_changes": [],
        "timeline_changes": [{"event": beat.name or f"Beat {beat.ordinal}", "scene": scene.title or "", "note": "由本节正文推进"}],
        "scene_summary": markdown[:300],
    }


def create_beat_delta(db: Session, story_id: str, chapter: Chapter, scene: Scene, beat: Beat, pv: ProseVersion, config=None) -> StateDelta:
    existing = db.scalar(select(StateDelta).where(StateDelta.scope_type == "beat", StateDelta.scope_id == beat.id))
    if existing is not None:
        return existing
    if config is None:
        config = get_ai_config(db, story_id)
    delta = StateDelta(story_id=story_id, chapter_id=chapter.id, scope_type="beat", scope_id=beat.id, source_version_id=pv.id, changes=json.dumps(_build_changes_from_prose(db, chapter, scene, beat, pv.markdown, config), ensure_ascii=False), status="proposed", check_result=json.dumps({"issues": []}, ensure_ascii=False))
    db.add(delta)
    db.commit()
    db.refresh(delta)
    return delta


def _ai_consistency_check(db: Session, chapter: Chapter, scene: Scene, beat: Beat, markdown: str, snapshot_state: dict[str, Any], config) -> list[dict[str, str]]:
    """AI-driven consistency findings (prose vs chapter-entry snapshot).

    Returns a list of {"rule", "severity", "evidence"} dicts; empty on any
    failure. Deterministic rules still run on top of these findings.
    """
    adapter = build_adapters().get(_model_for_config(config.model).provider)
    if adapter is None:
        return []
    messages = [
        {"role": "system", "content": compose_system_prompt(db, _model_for_config(config.model).provider, "consistency_check")},
        {"role": "user", "content": f"章节开始快照：{json.dumps(snapshot_state, ensure_ascii=False)[:2500]}\n\n场景：{scene.title or ''}\n节拍：{beat.name or f'Beat {beat.ordinal}'}\n\n正文：\n{markdown[:4000]}"},
    ]
    try:
        raw = adapter.complete(messages, temperature=0.1, reasoning_strength="low", json_mode=True, action="consistency_check")
        payload = extract_json(raw)
        if not isinstance(payload, list):
            return []
        findings = []
        for item in payload:
            if isinstance(item, dict) and item.get("rule"):
                findings.append({
                    "rule": str(item.get("rule"))[:120],
                    "severity": str(item.get("severity") or "warning"),
                    "evidence": str(item.get("evidence") or ""),
                })
        return findings
    except Exception:
        return []


def run_consistency_check(db: Session, story_id: str, chapter: Chapter, scene: Scene, beat: Beat, pv: ProseVersion, checkpoint: str = "beat", config=None) -> list[ConsistencyIssue]:
    """Run consistency checks on generated prose: AI (prose vs snapshot) + deterministic rules."""
    issues: list[ConsistencyIssue] = []
    markdown = pv.markdown
    if config is None:
        config = get_ai_config(db, story_id)
    # AI-driven prose-vs-snapshot conflict detection (never blocks on failure).
    snapshot = db.scalar(select(StateSnapshot).where(StateSnapshot.chapter_id == chapter.id))
    snapshot_state = json.loads(snapshot.state) if snapshot else {}
    for finding in _ai_consistency_check(db, chapter, scene, beat, markdown, snapshot_state, config):
        issues.append(ConsistencyIssue(
            story_id=story_id, chapter_id=chapter.id, checkpoint=checkpoint, scope_id=beat.id,
            rule=finding["rule"], severity=finding["severity"], evidence=finding["evidence"], status="open",
        ))
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
    # 独立 review 环节：判断本章产出是否需要更新蓝图（不阻塞，失败静默）
    try:
        config = get_ai_config(db, story_id)
        review_blueprint_updates(db, story_id, chapter, None, None, config, scope="chapter")
    except Exception:
        pass
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
