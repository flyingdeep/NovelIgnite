import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.config import Settings
from app.projects.models import Entity, GenerationTask, StateEntry, Story, StoryArtifact


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ModelGenerationError(Exception):
    pass


class ConceptModelAdapter(Protocol):
    provider: str
    display_name: str

    def generate_concept(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]: ...

    def generate_blueprint(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]: ...

    def generate_chapter_plan(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]: ...


class FakeModelAdapter:
    provider = "fake"
    display_name = "离线模拟（Fake）"
    def generate_concept(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if parameters.get("force_failure"):
            raise ModelGenerationError("model_unavailable")
        return {
            "genre": "待作者确认",
            "writing_style": "待作者确认",
            "estimated_length": "待作者确认",
            "narrative_perspective": "待作者确认",
            "synopsis": f"围绕“{idea}”展开的故事概念候选。",
            "core_theme": "待作者确认",
            "main_conflict": "待作者确认",
            "selling_points": ["由作者确认后写入 Story Concept"],
        }

    def generate_blueprint(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if parameters.get("force_failure"):
            raise ModelGenerationError("model_unavailable")
        return {
            "bible": {"characters": [], "world": {}, "initial_timeline": []},
            "arc": {"core_conflict": f"从“{idea}”提炼的冲突候选。", "stages": []},
            "living_state": {"character": [], "world": [], "timeline": []},
        }

    def generate_chapter_plan(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]:
        count = int(parameters.get("chapter_count", 6))
        return {
            "chapters": [
                {
                    "title": f"第 {ordinal} 章 · {title}",
                    "summary": summary,
                    "goal": goal,
                    "main_characters": [],
                    "arc_relation": arc_relation,
                }
                for ordinal, (title, summary, goal, arc_relation) in enumerate(
                    [
                        ("异常样本", "主角发现与自身有关的异常记忆样本。", "建立身份谜题。", "建立核心冲突。"),
                        ("黑市入口", "主角获得进入地下拍卖场的线索。", "进入危险世界。", "推进第一阶段。"),
                        ("记忆目录", "主角发现自己的记忆被分批拍卖。", "确认威胁。", "首次转折。"),
                        ("失控交易", "一次交易揭示更大的幕后势力。", "加深冲突。", "中段升级。"),
                        ("被抹去的人", "主角找回关键记忆并面对真相。", "揭示核心秘密。", "逼近高潮。"),
                        ("拍卖终局", "主角做出关于身份与记忆的选择。", "完成本阶段目标。", "阶段性结局。"),
                    ][:count],
                    start=1,
                )
            ]
        }


def _extract_json(content: Any) -> Any:
    """把模型返回内容解析为 JSON；支持直接对象、markdown 代码块包裹及夹杂解释文字的场景。"""
    if isinstance(content, dict):
        return content
    text = str(content).strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except ValueError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("no json object found")


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    display_name: str
    base_url: str
    api_key: str
    model_name: str
    supports_response_format: bool = True
    timeout: float = 180.0


class OpenAICompatibleModelAdapter:
    def __init__(self, spec: ModelSpec) -> None:
        self.spec = spec
        self.provider = spec.provider
        self.display_name = spec.display_name

    def generate_concept(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]:
        return self._generate(
            "你是一位资深中文小说策划。请把用户的创作意图整理为结构化的 Story Concept，"
            "全部字段用简体中文填写，必须只返回合法 JSON 对象，不要输出任何解释或其他文字。",
            idea,
            parameters,
        )

    def generate_blueprint(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]:
        return self._generate(
            "你是一位资深中文小说策划。请基于用户的创作意图生成 Story Blueprint，"
            "全部字段用简体中文填写，JSON 必须包含 bible、arc、living_state 三个顶层键，"
            "其中 bible 含 characters、world、initial_timeline，arc 含 core_conflict、stages，"
            "living_state 含 character、world、timeline，只返回合法 JSON 对象。",
            idea,
            parameters,
        )

    def generate_chapter_plan(self, idea: str, parameters: dict[str, Any]) -> dict[str, Any]:
        count = int(parameters.get("chapter_count", 6))
        return self._generate(
            "你是一位资深中文小说策划。请基于作者创意生成全书 Chapter Plan。"
            f"生成 {count} 章。必须只返回合法 JSON 对象，顶层键为 chapters；"
            "chapters 为数组，每项必须包含 title、summary、goal、main_characters（数组）、arc_relation。"
            "全部内容用简体中文，计划不是已发生事实。",
            idea,
            parameters,
        )

    def _generate(self, instruction: str, idea: str, parameters: dict[str, Any]) -> dict[str, Any]:
        spec = self.spec
        if not spec.base_url or not spec.api_key:
            raise ModelGenerationError("model_not_configured")
        body: dict[str, Any] = {
            "model": spec.model_name,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": idea},
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
        }
        if spec.supports_response_format:
            body["response_format"] = {"type": "json_object"}
        reserved = {"model", "messages", "provider"}
        body.update({key: value for key, value in parameters.items() if key not in reserved})
        try:
            response = httpx.post(
                f"{spec.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {spec.api_key}"},
                json=body,
                timeout=spec.timeout,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            payload = _extract_json(content)
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            raise ModelGenerationError("model_unavailable") from None
        if not isinstance(payload, dict):
            raise ModelGenerationError("invalid_model_output")
        return payload


def build_model_adapters(settings: Settings) -> dict[str, ConceptModelAdapter]:
    """构建全部已配置的模型适配器；仅配置了 API Key 的提供方才会启用。"""
    adapters: dict[str, ConceptModelAdapter] = {"fake": FakeModelAdapter()}
    specs = [
        ModelSpec(
            "agnes", "Agnes 2.0 Flash", settings.agnes_base_url, settings.agnes_api_key or "",
            settings.agnes_model, True, settings.model_timeout,
        ),
        ModelSpec(
            "deepseek", "DeepSeek V4 Flash", settings.deepseek_base_url, settings.deepseek_api_key or "",
            settings.deepseek_model, True, settings.model_timeout,
        ),
        ModelSpec(
            "grok", "Grok 4.5", settings.grok_base_url, settings.grok_api_key or "",
            settings.grok_model, False, settings.model_timeout,
        ),
    ]
    for spec in specs:
        if spec.api_key:
            adapters[spec.provider] = OpenAICompatibleModelAdapter(spec)
    return adapters


class ProjectService:
    def __init__(
        self,
        session: Session,
        model: ConceptModelAdapter | None = None,
        models: dict[str, ConceptModelAdapter] | None = None,
        default_provider: str = "fake",
    ) -> None:
        self.session = session
        if model is not None:
            self.models = {getattr(model, "provider", "fake"): model}
            self.default_provider = getattr(model, "provider", "fake")
        else:
            self.models = models or {"fake": FakeModelAdapter()}
            self.default_provider = default_provider

    def create_story(self, idea: str, title: str | None) -> Story:
        story = Story(title=title or "未命名故事", idea=idea)
        self.session.add(story)
        self.session.commit()
        self.session.refresh(story)
        return story

    def get_story(self, story_id: str) -> Story:
        story = self.session.get(Story, story_id)
        if story is None:
            raise NotFoundError()
        return story

    def generate_concept(self, story_id: str, parameters: dict[str, Any]) -> GenerationTask:
        return self._generate(story_id, "generate_concept", parameters)

    def generate_blueprint(self, story_id: str, parameters: dict[str, Any]) -> GenerationTask:
        return self._generate(story_id, "generate_blueprint", parameters)

    def generate_chapter_plan(self, story_id: str, parameters: dict[str, Any]) -> GenerationTask:
        return self._generate(story_id, "generate_chapter_plan", parameters)

    def _generate(self, story_id: str, action: str, parameters: dict[str, Any]) -> GenerationTask:
        story = self.get_story(story_id)
        if action == "generate_blueprint" and story.status != "concept_confirmed":
            raise ConflictError()
        if action == "generate_chapter_plan" and story.status != "blueprint_confirmed":
            raise ConflictError()
        params = dict(parameters)
        provider = params.pop("provider", None) or self.default_provider
        adapter = self.models.get(provider)
        if adapter is None:
            raise ModelGenerationError("model_not_configured")
        task = GenerationTask(
            story_id=story.id,
            action=action,
            input_ref={"story_id": story.id, "idea_length": len(story.idea)},
            model_snapshot={"provider": provider, "parameters": params},
            status="running",
        )
        self.session.add(task)
        try:
            task.output = getattr(adapter, action)(story.idea, params)
            task.status = "succeeded"
        except ModelGenerationError:
            task.status = "failed"
            task.failure_code = "model_unavailable"
            self.session.commit()
            raise
        self.session.commit()
        self.session.refresh(task)
        return task

    def list_models(self) -> list[dict[str, str]]:
        return [
            {"provider": provider, "display_name": getattr(adapter, "display_name", provider)}
            for provider, adapter in self.models.items()
        ]

    def confirm_blueprint(self, story_id: str) -> Story:
        story = self.get_story(story_id)
        if story.status != "blueprint_review":
            raise ConflictError()
        kinds = set(
            self.session.scalars(
                select(StoryArtifact.kind).where(
                    StoryArtifact.story_id == story_id,
                    StoryArtifact.kind.in_(("bible", "arc")),
                    StoryArtifact.status == "confirmed",
                )
            ).all()
        )
        if kinds != {"bible", "arc"}:
            raise ConflictError()
        story.status = "blueprint_confirmed"
        self.session.commit()
        self.session.refresh(story)
        return story

    def get_generation_task(self, story_id: str, task_id: str) -> GenerationTask:
        self.get_story(story_id)
        task = self.session.get(GenerationTask, task_id)
        if task is None or task.story_id != story_id:
            raise NotFoundError()
        return task

    def get_artifact(self, story_id: str, kind: str) -> StoryArtifact:
        self.get_story(story_id)
        artifact = self.session.scalar(
            select(StoryArtifact)
            .where(StoryArtifact.story_id == story_id, StoryArtifact.kind == kind)
            .order_by(StoryArtifact.version.desc())
        )
        if artifact is None:
            raise NotFoundError()
        return artifact

    def update_concept(
        self,
        story_id: str,
        payload: dict[str, Any],
        layer: str,
        locked_paths: list[str],
        expected_version: int,
        status: str,
    ) -> StoryArtifact:
        story = self.get_story(story_id)
        current = self.session.scalar(
            select(StoryArtifact)
            .where(StoryArtifact.story_id == story_id, StoryArtifact.kind == "concept")
            .order_by(StoryArtifact.version.desc())
        )
        current_version = current.version if current else 0
        if expected_version != current_version + 1:
            raise ConflictError()
        if current:
            for path in current.locked_paths:
                if current.payload.get(path) != payload.get(path):
                    raise ConflictError()
        artifact = StoryArtifact(
            story_id=story.id,
            kind="concept",
            layer=layer,
            payload=payload,
            status=status,
            locked_paths=sorted(set((current.locked_paths if current else []) + locked_paths)),
            version=current_version + 1,
        )
        self.session.add(artifact)
        if status == "confirmed":
            story.status = "concept_confirmed"
        self.session.commit()
        self.session.refresh(artifact)
        return artifact

    def update_blueprint_artifact(
        self,
        story_id: str,
        kind: str,
        payload: dict[str, Any],
        layer: str,
        locked_paths: list[str],
        expected_version: int,
        status: str,
    ) -> StoryArtifact:
        if kind not in {"bible", "arc", "living_state"}:
            raise NotFoundError()
        if kind == "living_state" and layer != "living":
            raise ValueError("living_state_requires_living_layer")
        if kind != "living_state" and layer != "baseline":
            raise ValueError("baseline_artifact_requires_baseline_layer")
        story = self.get_story(story_id)
        if story.status not in {"concept_confirmed", "blueprint_review"}:
            raise ConflictError()
        current = self.session.scalar(
            select(StoryArtifact)
            .where(StoryArtifact.story_id == story_id, StoryArtifact.kind == kind)
            .order_by(StoryArtifact.version.desc())
        )
        current_version = current.version if current else 0
        if expected_version != current_version + 1:
            raise ConflictError()
        if current:
            for path in current.locked_paths:
                if current.payload.get(path) != payload.get(path):
                    raise ConflictError()
        artifact = StoryArtifact(
            story_id=story.id,
            kind=kind,
            layer=layer,
            payload=payload,
            status=status,
            locked_paths=sorted(set((current.locked_paths if current else []) + locked_paths)),
            version=current_version + 1,
        )
        self.session.add(artifact)
        story.status = "blueprint_review"
        self.session.commit()
        self.session.refresh(artifact)
        return artifact

    def create_entity(
        self, story_id: str, entity_type: str, name: str, canonical_data: dict[str, Any], lock_state: str
    ) -> Entity:
        self.get_story(story_id)
        existing = self.session.scalar(
            select(Entity).where(Entity.story_id == story_id, Entity.type == entity_type, Entity.name == name)
        )
        if existing:
            raise ConflictError()
        entity = Entity(
            story_id=story_id,
            type=entity_type,
            name=name,
            canonical_data=canonical_data,
            lock_state=lock_state,
        )
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update_entity(
        self, story_id: str, entity_id: str, canonical_data: dict[str, Any], lock_state: str, expected_version: int
    ) -> Entity:
        self.get_story(story_id)
        entity = self.session.get(Entity, entity_id)
        if entity is None or entity.story_id != story_id:
            raise NotFoundError()
        if entity.version != expected_version or (entity.lock_state == "locked" and entity.canonical_data != canonical_data):
            raise ConflictError()
        entity.canonical_data = canonical_data
        entity.lock_state = lock_state
        entity.version += 1
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def create_state_entry(self, story_id: str, **data: Any) -> StateEntry:
        self.get_story(story_id)
        subject_id = data.get("subject_id")
        if subject_id:
            subject = self.session.get(Entity, subject_id)
            if subject is None or subject.story_id != story_id:
                raise NotFoundError()
        entry = StateEntry(story_id=story_id, **data)
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def list_state_entries(self, story_id: str) -> dict[str, list[StateEntry]]:
        self.get_story(story_id)
        entries = self.session.scalars(
            select(StateEntry).where(StateEntry.story_id == story_id).order_by(StateEntry.created_at)
        ).all()
        grouped: dict[str, list[StateEntry]] = {"character": [], "world": [], "timeline": []}
        for entry in entries:
            grouped[entry.domain].append(entry)
        return grouped
