"""Blueprint baseline/living-state service."""
from __future__ import annotations

import json
import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.model_adapter import build_adapters, configured_model_specs, extract_json
from app.infrastructure.model_prompt_profiles import compose_system_prompt
from app.infrastructure.prompts import prompt_version, system_prompt
from app.works.blueprint_schemas import BlueprintConfirm, BlueprintGenerationRequest, BlueprintUpdate
from app.works.concept_service import _model_for_config
from app.works.models import GenerationTask, StoryArtifact
from app.works.service import get_ai_config, get_story_or_404

BLUEPRINT_KINDS = ("characters", "world", "timeline", "arc")


def _json(artifact: StoryArtifact | None, fallback):
    return json.loads(artifact.payload) if artifact else fallback


def latest_blueprint(db: Session, story_id: str, kind: str) -> StoryArtifact | None:
    return db.scalar(select(StoryArtifact).where(StoryArtifact.story_id == story_id, StoryArtifact.kind == kind).order_by(StoryArtifact.version.desc()))


_BLUEPRINT_CONTEXT_LABELS = {"concept": "已确认故事概念", "characters": "核心人物", "world": "世界设定", "timeline": "时间线与前史", "arc": "剧情弧与伏笔"}


def build_blueprint_context(db: Session, story_id: str, *, max_chars: int = 6000) -> str:
    """把作者原始创作意图 + 已确认 Blueprint（概念 + characters/world/timeline/arc）序列化为紧凑上下文文本。

    供章节计划 / 场景计划 / 节拍计划 / 正文生成等所有生成环节注入，确保模型基于
    权威设定创作，杜绝自创与蓝图冲突的角色、组织与地名（设定不一致的根因）。
    作者原始创作意图置于最前且优先保证完整，任何生成都不得删减其中已给出的细节。
    """
    story = get_story_or_404(db, story_id)
    idea_block = ""
    if story.idea_text and story.idea_text.strip():
        idea_block = f"【作者原始创作意图（最高优先级，任何生成都不得删减、简化或违背其中已给出的细节）】\n{story.idea_text}"
    parts: list[str] = []
    for kind in ("concept", "characters", "world", "timeline", "arc"):
        artifact = latest_blueprint(db, story_id, kind)
        payload = _json(artifact, None)
        if not payload:
            continue
        # 排除内部元数据（如 AI 自动应用的 _ai_updates），不进入模型上下文。
        if isinstance(payload, dict):
            payload = {k: v for k, v in payload.items() if k != "_ai_updates"}
        text = json.dumps(payload, ensure_ascii=False)
        parts.append(f"【{_BLUEPRINT_CONTEXT_LABELS.get(kind, kind)}】\n{text}")
    joined = "\n\n".join(parts)
    if idea_block:
        joined = idea_block + "\n\n" + joined
    if max_chars and len(joined) > max_chars:
        # 优先保证作者原始意图完整；超限时只截断蓝图部分。
        if idea_block and len(idea_block) >= max_chars:
            return idea_block[:max_chars]
        if idea_block:
            budget = max_chars - len(idea_block) - 2
            joined = idea_block + "\n\n" + (joined[len(idea_block) + 2:][:max(0, budget)] or "") + "\n…（设定较长已截断，后续内容以蓝图为准）"
        else:
            joined = joined[:max_chars] + "\n…（设定较长已截断，后续内容以蓝图为准）"
    return joined


_WORLD_ORG_HINTS = ("组织", "集团", "势力", "帮派", "社团", "协会", "联盟", "家族", "财阀")
_WORLD_RULE_HINTS = ("规则", "法则", "体系", "世界背景")


def build_focused_blueprint_context(db: Session, story_id: str, *, pov: str = "", location: str = "", max_chars: int = 14000) -> str:
    """正文生成专用：聚焦当前场景的蓝图上下文（减少设定密度对行文的挤压）。

    与 build_blueprint_context 的区别（A·减法 + 针对性）：
    - 概念：完整；
    - characters：全部人物（一致性权威，防止模型自创），当前 POV 人物置于最前并标注；
    - world：仅保留与当前 location 命中的地点条目 + 组织/势力条目 + 世界规则条目（防自创）；
      若 location 无任何命中则保留全部（宁可冗余也不让模型自创地点/规则）；
    - timeline / arc：完整（条目通常较少）；
    - living 投影不进入正文上下文；作者原始创作意图仍置顶且优先保证完整。
    """
    story = get_story_or_404(db, story_id)
    idea_block = ""
    if story.idea_text and story.idea_text.strip():
        idea_block = f"【作者原始创作意图（最高优先级，任何生成都不得删减、简化或违背其中已给出的细节）】\n{story.idea_text}"
    parts: list[str] = []

    concept = latest_blueprint(db, story_id, "concept")
    if concept:
        cp = json.loads(concept.payload)
        if isinstance(cp, dict):
            cp = {k: v for k, v in cp.items() if k != "_ai_updates"}
        parts.append(f"【已确认故事概念】\n{json.dumps(cp, ensure_ascii=False)}")

    chars = latest_blueprint(db, story_id, "characters")
    if chars:
        cp = json.loads(chars.payload)
        if not isinstance(cp, dict):
            cp = {}
        entries = cp.get("entries") or []
        if pov and entries:
            entries = sorted(entries, key=lambda e: 0 if str(e.get("name", "")) == pov else 1)
        parts.append(f"【核心人物】（当前 POV：{pov or '未指定'}）\n{json.dumps({'title': cp.get('title', ''), 'entries': entries}, ensure_ascii=False)}")

    world = latest_blueprint(db, story_id, "world")
    if world:
        wp = json.loads(world.payload)
        if not isinstance(wp, dict):
            wp = {}
        wentries: list[Any] = []
        for e in wp.get("entries") or []:
            if not isinstance(e, dict):
                continue
            name = str(e.get("name") or "")
            role = str(e.get("role") or "")
            text = name + role + "".join(str(v) for v in (e.get("fields") or {}).values())
            if location and location in text:
                wentries.append(e)
                continue
            if any(h in role or h in name for h in _WORLD_ORG_HINTS) or any(h in name or h in role for h in _WORLD_RULE_HINTS):
                wentries.append(e)
        if not wentries:
            wentries = wp.get("entries") or []
        parts.append(f"【世界设定】（当前地点：{location or '未指定'}）\n{json.dumps({'title': wp.get('title', ''), 'entries': wentries}, ensure_ascii=False)}")

    for kind, label in (("timeline", "时间线与前史"), ("arc", "剧情弧与伏笔")):
        artifact = latest_blueprint(db, story_id, kind)
        if artifact:
            ap = json.loads(artifact.payload)
            if isinstance(ap, dict):
                ap = {k: v for k, v in ap.items() if k != "_ai_updates"}
            parts.append(f"【{label}】\n{json.dumps(ap, ensure_ascii=False)}")

    joined = "\n\n".join(parts)
    if idea_block:
        joined = idea_block + "\n\n" + joined
    if max_chars and len(joined) > max_chars:
        if idea_block and len(idea_block) >= max_chars:
            return idea_block[:max_chars]
        if idea_block:
            budget = max_chars - len(idea_block) - 2
            joined = idea_block + "\n\n" + (joined[len(idea_block) + 2:][:max(0, budget)] or "") + "\n…（设定较长已截断，后续内容以蓝图为准）"
        else:
            joined = joined[:max_chars] + "\n…（设定较长已截断，后续内容以蓝图为准）"
    return joined


def list_blueprint(db: Session, story_id: str) -> dict[str, dict[str, Any] | None]:
    get_story_or_404(db, story_id)
    return {kind: latest_blueprint(db, story_id, kind) for kind in (*BLUEPRINT_KINDS, "living_state")}


def list_living_state_history(db: Session, story_id: str) -> list[StoryArtifact]:
    """All Living State versions, newest first (for the version-history modal)."""
    get_story_or_404(db, story_id)
    return list(db.scalars(select(StoryArtifact).where(StoryArtifact.story_id == story_id, StoryArtifact.kind == "living_state").order_by(StoryArtifact.version.desc())))


def list_blueprint_kind_history(db: Session, story_id: str, kind: str) -> list[StoryArtifact]:
    """某分类（characters/world/timeline/arc）的全部版本，新旧排序，供「更新履历」追溯。"""
    get_story_or_404(db, story_id)
    if kind not in BLUEPRINT_KINDS:
        raise HTTPException(status_code=422, detail=f"Unknown blueprint kind: {kind}")
    return list(db.scalars(select(StoryArtifact).where(StoryArtifact.story_id == story_id, StoryArtifact.kind == kind).order_by(StoryArtifact.version.desc())))


def list_blueprint_reviews(db: Session, story_id: str) -> list[dict[str, Any]]:
    """列出所有待作者确认的蓝图更新建议（最新在前）。"""
    get_story_or_404(db, story_id)
    artifacts = list(db.scalars(select(StoryArtifact).where(StoryArtifact.story_id == story_id, StoryArtifact.kind == "blueprint_review").order_by(StoryArtifact.version.desc())))
    out: list[dict[str, Any]] = []
    for artifact in artifacts:
        payload = json.loads(artifact.payload) if artifact.payload else {}
        out.append({
            "id": artifact.id,
            "version": artifact.version,
            "status": artifact.status,
            "scope": payload.get("scope", ""),
            "chapter_ordinal": payload.get("chapter_ordinal"),
            "scene_id": payload.get("scene_id"),
            "suggestions": payload.get("suggestions", []),
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        })
    return out


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
            _normalize_kind_entries(source)
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
            _normalize_kind_entries(mapped)
            return mapped, False
    fallback = fallback_blueprint(idea, concept)
    _normalize_kind_entries(fallback)
    return fallback, True


def _blueprint_scale_for_length(length: str) -> str:
    """按概念预计篇幅给出蓝图信息量档位，使设定规模与文章长短匹配。"""
    low = (length or "").lower()
    if any(k in low for k in ("短篇", "短片", "短剧", "短")):
        return "本作篇幅较短：请精简设定——总出场人物 3-6 人，世界 2-3 个地点、1-2 个组织，时间线 1-2 条关键前史，剧情弧单主线即可。"
    if any(k in low for k in ("长篇", "长剧", "长片", "十万", "几十万")):
        return "本作为长篇/复杂剧情：请充实设定——总出场人物 12-20 人（主角/盟友宿敌/反派核心/支线配角分层），世界观 3-4 个功能区域、3-5 个组织势力与制衡关系，时间线 3-5 条关键前史，剧情弧主线 + 2-3 条支线/暗线。"
    return "本作篇幅中等：设定适度——总出场人物 6-12 人，世界 3 个功能区域、2-3 个组织，时间线 2-3 条关键前史，剧情弧主线 + 1 条支线。"


_FIELD_KEYWORDS = (
    "性格特质", "性格", "职业身份", "职业", "身份", "动机", "目标", "缺陷",
    "欲望与软肋", "软肋", "欲望", "初始关系", "核心关系", "关系", "背景故事", "背景",
    "秘密与伏笔", "秘密", "伏笔", "能力与限制", "能力", "创作约束", "约束",
    "外貌", "形象", "关键事件", "结局", "规则", "设定",
)


def _fields_from_string(text: str) -> dict[str, str]:
    """把模型输出的字符串 fields（如「性格…；职业身份为…」）拆成 {label: value}。

    按分号/句号切段，逐段提取标签：优先取「为/是/：」前的短词，其次匹配已知
    字段关键词前缀，兜底用「设定N」。避免把整个字符串塞进单个字段或逐字拆散。
    """
    text = (text or "").strip()
    if not text:
        return {"设定": ""}
    segments = [s.strip() for s in re.split(r"[；;。\n]", text) if s.strip()]
    out: dict[str, str] = {}
    counter = 1
    for seg in segments:
        label: str | None = None
        value: str = seg
        m = re.match(r"^(.{1,8}?)[为是:：](.+)$", seg)
        if m:
            label, value = m.group(1).strip(), m.group(2).strip()
            if not value:
                label, value = None, seg
        if label is None:
            matched = next((k for k in _FIELD_KEYWORDS if seg.startswith(k)), None)
            if matched:
                label, value = matched, seg[len(matched):].lstrip("为是:：、， ")
            else:
                label = f"设定{counter}"
                counter += 1
        key = label
        while key in out:
            key = f"{label}{counter}"
            counter += 1
        out[key] = value
    return out or {"设定": text}


def _normalize_fields(fields: Any) -> dict[str, str]:
    """把模型输出的 fields 规范化为 {label: value} 字典（兼容 dict / 二维数组 / 字符串）。"""
    if isinstance(fields, dict):
        out: dict[str, str] = {}
        for k, v in fields.items():
            out[str(k)] = v if isinstance(v, str) else ("；".join(str(x) for x in v) if isinstance(v, (list, tuple)) else str(v))
        return out
    if isinstance(fields, (list, tuple)):
        out = {}
        for f in fields:
            if isinstance(f, (list, tuple)) and len(f) >= 2:
                k, v = str(f[0]), f[1]
                out[k] = v if isinstance(v, str) else ("；".join(str(x) for x in v) if isinstance(v, (list, tuple)) else str(v))
            elif f is not None:
                out[str(f)] = ""
        return out or {"设定": ""}
    if isinstance(fields, str):
        return _fields_from_string(fields)
    return {"设定": ""}


def _normalize_kind_entries(payload: dict[str, dict[str, Any]]) -> None:
    """规范化四个 kind 中每个 entry 的 fields，保证入库结构稳定为 {label: value}。"""
    for kind in BLUEPRINT_KINDS:
        block = payload.get(kind)
        if not isinstance(block, dict):
            continue
        entries = block.get("entries")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry["fields"] = _normalize_fields(entry.get("fields"))


def generate_blueprint(db: Session, story_id: str, request: BlueprintGenerationRequest) -> list[StoryArtifact]:
    story = get_story_or_404(db, story_id)
    if story.stage not in {"concept_confirmed", "blueprint_review", "blueprint_confirmed"}:
        raise HTTPException(status_code=409, detail="Concept must be confirmed before Blueprint generation")
    config = get_ai_config(db, story_id)
    spec = _model_for_config(request.model or config.model)
    concept = latest_blueprint(db, story_id, "concept")
    concept_payload = _json(concept, {})
    task = GenerationTask(story_id=story.id, action="generate_blueprint", target_type="story", model_snapshot=json.dumps({"model": config.model, "temperature": config.temperature, "reasoning_strength": config.reasoning_strength}, ensure_ascii=False), prompt_version=prompt_version("generate_blueprint"), input_ref=json.dumps({"story_id": story.id, "concept_version": concept.version if concept else None}, ensure_ascii=False), status="running")
    db.add(task)
    db.flush()
    messages = [
        {"role": "system", "content": compose_system_prompt(db, spec.provider, "generate_blueprint")},
        {"role": "user", "content": f"根据已确认故事概念与作者创意生成全局 Blueprint。{_blueprint_scale_for_length(str(concept_payload.get('length') or ''))}只生成稳定 Baseline，不生成章节状态。Concept：{json.dumps(concept_payload, ensure_ascii=False)} Idea：{story.idea_text}"},
    ]
    try:
        adapter = build_adapters().get(spec.provider)
        if adapter:
            raw_payload = extract_json(adapter.complete(messages, temperature=config.temperature, reasoning_strength=config.reasoning_strength, json_mode=True, action="generate_blueprint"))
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
        living_domains: dict[str, Any] = {}
        for kind, artifact in zip(BLUEPRINT_KINDS, artifacts):
            state = json.loads(artifact.payload)
            _normalize_kind_entries({kind: state})
            living_domains[kind] = {"source_ref": artifact.id, "version": artifact.version, "state": state}
        living_payload = {
            "source": "initial_story_state",
            "temporal_scope": "story_start",
            "certainty": "confirmed",
            "context_policy": "always",
            "domains": living_domains,
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
