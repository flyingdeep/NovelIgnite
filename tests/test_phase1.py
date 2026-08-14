import json

import pytest

from app.infrastructure.model_adapter import ModelSpec, OpenAICompatibleAdapter, extract_json
from app.infrastructure.fake_adapter import FakeModelAdapter


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


def _capture_adapter_kwargs(monkeypatch, spec, **complete_kwargs):
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "ok"})()})()]})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv(spec.api_key_env, "test")
    monkeypatch.setattr("openai.OpenAI", FakeClient)
    OpenAICompatibleAdapter(spec).complete([{"role": "user", "content": "hi"}], **complete_kwargs)
    return captured


def test_models_endpoint_has_three_specs(client):
    models = client.get("/api/v1/models").json()
    assert {model["provider"] for model in models} == {"agnes", "deepseek", "grok"}
    assert next(model for model in models if model["provider"] == "grok")["supports_json"] is False


def test_extract_json_handles_code_fence_and_wrapping():
    assert extract_json('```json\n{"ok": true}\n```')["ok"] is True
    assert extract_json('result: {"count": 2}') == {"count": 2}


def test_agnes_spec_upgraded_to_25():
    from app.infrastructure.model_adapter import MODEL_SPECS

    agnes = next(spec for spec in MODEL_SPECS if spec.provider == "agnes")
    assert agnes.model == "agnes-2.5-flash"
    assert agnes.name == "Agnes 2.5 Flash"


def test_model_max_output_tokens_from_official_docs():
    from app.infrastructure.model_adapter import MODEL_SPECS

    limits = {spec.provider: spec.max_output_tokens for spec in MODEL_SPECS}
    assert limits["agnes"] == 65536  # Agnes 2.5 Flash：最大输出 65.5K
    assert limits["deepseek"] == 384000  # DeepSeek v4-flash：最大输出 384K
    assert limits["grok"] == 500000  # Grok 4.5：500K


def test_adapter_uses_spec_max_tokens_by_default(monkeypatch):
    from app.infrastructure.model_adapter import MODEL_SPECS

    spec = next(s for s in MODEL_SPECS if s.provider == "deepseek")
    captured = _capture_adapter_kwargs(monkeypatch, spec, json_mode=True)
    assert captured["max_tokens"] == 384000


def test_deepseek_thinking_params(monkeypatch):
    from app.infrastructure.model_adapter import MODEL_SPECS

    spec = next(s for s in MODEL_SPECS if s.provider == "deepseek")
    captured = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="medium")
    assert captured["extra_body"]["thinking"] == {"type": "enabled"}
    assert captured["reasoning_effort"] == "high"  # 官方映射表：medium -> high
    captured_low = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="low")
    assert captured_low["reasoning_effort"] == "low"


def test_agnes_thinking_params(monkeypatch):
    from app.infrastructure.model_adapter import MODEL_SPECS

    spec = next(s for s in MODEL_SPECS if s.provider == "agnes")
    captured = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="high")
    assert captured["extra_body"]["chat_template_kwargs"] == {"enable_thinking": True}
    captured_low = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="low")
    assert captured_low["extra_body"]["chat_template_kwargs"] == {"enable_thinking": False}


def test_grok_adapter_does_not_send_response_format(monkeypatch):
    spec = ModelSpec("grok", "Grok 4.5", "grok-4.5", "https://modelflare.dev/v1", "GROK_API_KEY", False, "grok")
    captured = _capture_adapter_kwargs(monkeypatch, spec, json_mode=True, reasoning_strength="medium")
    assert "response_format" not in captured
    assert captured["reasoning_effort"] == "medium"  # 顶层参数
    assert "extra_body" not in captured


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


def test_observability_records_generation_and_snapshot():
    from app.infrastructure import observability

    before = observability.snapshot()["generations"]["total"]
    observability.record_generation("generate_concept", "deepseek", succeeded=True, duration_ms=120.5, tokens={"prompt": 10, "completion": 20})
    observability.record_generation("generate_blueprint", "agnes", succeeded=False, duration_ms=3000.0, error_type="TimeoutError")
    snap = observability.snapshot()
    gens = snap["generations"]
    assert gens["total"] >= before + 2
    assert gens["by_action"]["generate_concept"]["succeeded"] == 1
    assert gens["by_action"]["generate_blueprint"]["failed"] == 1
    assert snap["errors"].get("TimeoutError", 0) >= 1
    assert snap["requests"]["total"] >= 0
    assert "recent_events" in snap


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "generations" in body
    assert "requests" in body
    assert "recent_events" in body


def test_concept_selling_points_normalized_to_list(client, monkeypatch):
    raw = '{"genre":"悬疑","summary":"测试梗概","selling_points":"卖点一；卖点二\\n卖点三"}'
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {"deepseek": FakeModelAdapter(raw)})
    created = client.post("/api/v1/works", json={}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "测试创意", "expected_version": created["version"]})
    generated = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"})
    assert generated.status_code == 200
    selling = generated.json()["artifact"]["payload"]["selling_points"]
    assert isinstance(selling, list)
    assert selling == ["卖点一", "卖点二", "卖点三"]


def test_chapter_fallback_has_no_demo_content():
    from app.planning.service import fallback_chapters
    chapters = fallback_chapters("一个老木匠在沙漠里雕刻钟")
    assert len(chapters) == 6
    blob = json.dumps(chapters, ensure_ascii=False)
    for banned in ("林墨", "监管局", "拍卖", "沈砚", "鉴定"):
        assert banned not in blob
    assert "老木匠" in blob or "沙漠" in blob


def test_chapter_plan_normalize_object_wrapper():
    from app.planning.service import _normalize_chapter_plan

    wrapped = {"chapters": [{"title": "第一章", "goal": "g", "summary": "s", "main_characters": ["焰"], "arc_role": "主线"}, {"title": "第二章"}]}
    result = _normalize_chapter_plan(wrapped, "idea")
    assert result is not None and len(result) == 2
    assert result[1]["title"] == "第二章"
    assert result[0]["main_characters"] == ["焰"]
    assert _normalize_chapter_plan({"foo": "bar"}, "idea") is None
    assert _normalize_chapter_plan("not a list", "idea") is None


def test_chapter_plan_tolerates_object_wrapped_response(client, monkeypatch):
    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    monkeypatch.setattr("app.works.blueprint_service.build_adapters", lambda: {})
    raw = '{"chapters": [{"title":"第一章","goal":"g1","summary":"s1","main_characters":["焰"],"arc_role":"主线"},{"title":"第二章","goal":"g2","summary":"s2"}]}'
    monkeypatch.setattr("app.planning.service.build_adapters", lambda: {"deepseek": FakeModelAdapter(raw)})
    created = client.post("/api/v1/works", json={"title": "章节包装"}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "猫狗故事", "expected_version": created["version"]})
    concept = client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"}).json()["artifact"]
    client.post(f"/api/v1/stories/{story_id}/concept/confirm", json={"expected_version": concept["version"]})
    blueprints = client.post(f"/api/v1/stories/{story_id}/blueprint/generations", json={"action": "generate_blueprint"}).json()["artifacts"]
    client.post(f"/api/v1/stories/{story_id}/blueprint/confirm", json={"expected_versions": {a["kind"]: a["version"] for a in blueprints}})
    generated = client.post(f"/api/v1/stories/{story_id}/chapter-plan", json={"action": "generate_chapter_plan"})
    assert generated.status_code == 200
    chapters = generated.json()["chapters"]
    assert len(chapters) == 2
    assert chapters[0]["title"] == "第一章"
    assert chapters[0]["access_status"] == "active"
    assert chapters[1]["access_status"] == "locked"
