from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database import Base, get_db
from app.main import app
from app.infrastructure.model_adapter import ModelSpec, OpenAICompatibleAdapter, extract_json
from app.infrastructure.fake_adapter import FakeModelAdapter


@pytest.fixture()
def client(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_works_crud_and_soft_delete(client):
    created = client.post("/api/v1/works", json={"title": "测试作品"})
    assert created.status_code == 201
    work = created.json()
    assert work["stage"] == "idea"
    assert client.get("/api/v1/works").json()[0]["id"] == work["id"]

    assert client.delete(f"/api/v1/works/{work['id']}").status_code == 204
    assert client.get("/api/v1/works").json() == []
    assert client.get(f"/api/v1/works/{work['id']}").status_code == 404


def test_idea_optimistic_lock(client):
    work = client.post("/api/v1/works", json={"title": "锁定测试"}).json()
    updated = client.put(f"/api/v1/stories/{work['id']}/idea", json={"idea_text": "原始创意", "expected_version": 1})
    assert updated.status_code == 200
    assert client.put(f"/api/v1/stories/{work['id']}/idea", json={"idea_text": "冲突", "expected_version": 1}).status_code == 409


def test_ai_config_validation_and_version(client):
    work = client.post("/api/v1/works", json={"title": "配置测试"}).json()
    config = client.get(f"/api/v1/stories/{work['id']}/ai-config").json()
    response = client.put(f"/api/v1/stories/{work['id']}/ai-config", json={"model": "Grok 4.5", "temperature": 1.2, "reasoning_strength": "high", "expected_version": config["version"]})
    assert response.status_code == 200
    assert response.json()["model"] == "Grok 4.5"
    assert client.put(f"/api/v1/stories/{work['id']}/ai-config", json={"model": "Grok 4.5", "temperature": 2, "reasoning_strength": "high", "expected_version": 2}).status_code == 422


def test_models_endpoint_has_three_specs(client):
    models = client.get("/api/v1/models").json()
    assert {model["provider"] for model in models} == {"agnes", "deepseek", "grok"}
    assert next(model for model in models if model["provider"] == "grok")["supports_json"] is False


def test_extract_json_handles_code_fence_and_wrapping():
    assert extract_json('```json\n{"ok": true}\n```')["ok"] is True
    assert extract_json('result: {"count": 2}') == {"count": 2}


def test_grok_adapter_does_not_send_response_format(monkeypatch):
    spec = ModelSpec("grok", "Grok 4.5", "grok-4.5", "https://modelflare.dev/v1", "GROK_API_KEY", False)
    adapter = OpenAICompatibleAdapter(spec)
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "ok"})()})()]})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv("GROK_API_KEY", "test")
    monkeypatch.setattr("openai.OpenAI", FakeClient)
    assert adapter.complete([{"role": "user", "content": "hi"}], json_mode=True) == "ok"
    assert "response_format" not in captured


def test_fake_adapter_is_deterministic_and_records_parameters():
    adapter = FakeModelAdapter('{"candidate": "ok"}')
    assert adapter.complete([], temperature=1.1, reasoning_strength="high", json_mode=True) == '{"candidate": "ok"}'
    assert adapter.calls[0]["temperature"] == 1.1
    assert adapter.calls[0]["reasoning_strength"] == "high"
    assert adapter.calls[0]["json_mode"] is True


def test_concept_candidate_edit_confirm_and_idea_lock(client, monkeypatch):
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    created = client.post("/api/v1/works", json={"title": "Concept 流程"}).json()
    story_id = created["id"]
    idea = client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "一位能听见墙壁心跳的人。", "expected_version": created["version"]})
    assert idea.status_code == 200

    generated = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"})
    assert generated.status_code == 200
    candidate = generated.json()["artifact"]
    assert candidate["status"] == "candidate"

    assert client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "不可修改", "expected_version": idea.json()["version"]}).status_code == 409
    edited = client.put(f"/api/v1/stories/{story_id}/concept", json={"payload": {**candidate["payload"], "style": "冷静深沉"}, "locked_paths": ["genre"], "expected_version": candidate["version"]})
    assert edited.status_code == 200

    confirmed = client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": edited.json()["version"]})
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": confirmed.json()["version"]}).status_code == 409


def test_blueprint_categories_edit_and_confirm(client, monkeypatch):
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    created = client.post("/api/v1/works", json={"title": "Blueprint 流程"}).json()
    story_id = created["id"]
    idea = client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "一位失忆调查员寻找真相。", "expected_version": created["version"]}).json()
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    assert client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]}).status_code == 200

    generated = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"})
    assert generated.status_code == 200
    artifacts = {item["kind"]: item for item in generated.json()["artifacts"]}
    assert set(artifacts) == {"characters", "world", "timeline", "arc"}

    characters = artifacts["characters"]
    edited = client.put(f"/api/v1/stories/{story_id}/blueprint/characters", json={"payload": {**characters["payload"], "author_note": "locked"}, "locked_paths": ["author_note"], "expected_version": characters["version"]})
    assert edited.status_code == 200
    versions = {kind: artifact["version"] for kind, artifact in artifacts.items()}
    versions["characters"] = edited.json()["version"]
    confirmed = client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": versions})
    assert confirmed.status_code == 200
    assert client.get(f"/api/v1/works/{story_id}").json()["stage"] == "blueprint_confirmed"
    living = client.get(f"/api/v1/stories/{story_id}/blueprint").json()["living_state"]
    assert living["layer"] == "living"
    assert living["status"] == "confirmed"
    assert set(living["payload"]["domains"]) == {"characters", "world", "timeline", "arc"}
    assert client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": versions}).status_code == 409


def test_chapter_plan_activation_and_locked_access(client, monkeypatch):
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.planning.service.build_adapters", lambda: {})
    created = client.post("/api/v1/works", json={"title": "Chapter Plan 流程"}).json()
    story_id = created["id"]
    idea = client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "调查员追查秘密。", "expected_version": created["version"]}).json()
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": {artifact["kind"]: artifact["version"] for artifact in blueprints}})
    generated = client.post(f"/api/v1/stories/{story_id}/chapter-plan", json={"action": "generate_chapter_plan"})
    assert generated.status_code == 200
    chapters = generated.json()["chapters"]
    assert chapters[0]["plan_status"] == "fixed"
    assert chapters[0]["access_status"] == "active"
    assert all(chapter["access_status"] == "locked" for chapter in chapters[1:])
    assert client.put(f"/api/v1/stories/{story_id}/chapters/{chapters[1]['id']}/plan", json={"summary": "禁止修改", "expected_version": chapters[1]["version"]}).status_code == 409


TITLE_CONCEPT_JSON = '{"genre":"悬疑","style":"冷静","length":"中篇","viewpoint":"第三人称","summary":"测试梗概","theme":"测试主题","conflict":"测试冲突","selling_points":["点1"],"title":"暗涌之城"}'


def test_title_auto_generated_on_concept_confirm(client, monkeypatch):
    fake = FakeModelAdapter(TITLE_CONCEPT_JSON)
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {"deepseek": fake})
    created = client.post("/api/v1/works", json={}).json()
    assert created["title"] == "未命名故事"
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "测试创意", "expected_version": created["version"]})
    generated = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"})
    assert generated.status_code == 200
    candidate = generated.json()["artifact"]
    confirmed = client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": candidate["version"]})
    assert confirmed.status_code == 200
    work = client.get(f"/api/v1/works/{story_id}").json()
    assert work["title"] == "暗涌之城"
    assert work["stage"] == "concept_confirmed"


def test_title_not_overwritten_when_already_named(client, monkeypatch):
    fake = FakeModelAdapter(TITLE_CONCEPT_JSON)
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {"deepseek": fake})
    created = client.post("/api/v1/works", json={"title": "作者自定书名"}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "测试创意", "expected_version": created["version"]})
    generated = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"})
    candidate = generated.json()["artifact"]
    confirmed = client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": candidate["version"]})
    assert confirmed.status_code == 200
    assert client.get(f"/api/v1/works/{story_id}").json()["title"] == "作者自定书名"


def test_title_update_and_version_conflict(client):
    created = client.post("/api/v1/works", json={"title": "旧名"}).json()
    story_id = created["id"]
    updated = client.put(f"/api/v1/stories/{story_id}/title", json={"title": "新名", "expected_version": created["version"]})
    assert updated.status_code == 200
    assert updated.json()["title"] == "新名"
    assert updated.json()["version"] == created["version"] + 1
    conflict = client.put(f"/api/v1/stories/{story_id}/title", json={"title": "再改", "expected_version": created["version"]})
    assert conflict.status_code == 409
