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
            if kwargs.get("stream"):
                chunk = type("Chunk", (), {"choices": [type("Choice", (), {"delta": type("Delta", (), {"content": "ok"})()})()]})()
                return iter([chunk])
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "ok"})()})()]})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv(spec.api_key_env, "test")
    monkeypatch.setattr("openai.OpenAI", FakeClient)
    OpenAICompatibleAdapter(spec).complete([{"role": "user", "content": "hi"}], **complete_kwargs)
    return captured


def test_models_endpoint_has_four_specs(client):
    models = client.get("/api/v1/models").json()
    assert {model["provider"] for model in models} == {"agnes", "deepseek", "grok", "ollama"}
    assert next(model for model in models if model["provider"] == "grok")["supports_json"] is False
    assert next(model for model in models if model["provider"] == "ollama")["supports_json"] is True


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


def test_ollama_spec_registered():
    from app.infrastructure.model_adapter import MODEL_SPECS

    ollama = next(spec for spec in MODEL_SPECS if spec.provider == "ollama")
    assert ollama.name == "Qwen3.6 Abliterated 27B (Ollama)"
    assert ollama.model == "huihui_aiQwen3.6-abliterated-27b:latest"
    assert ollama.base_url == "http://106.75.216.144:11434/v1"
    assert ollama.supports_json is True
    assert ollama.thinking == "ollama"
    assert ollama.max_output_tokens >= 65536


def test_ollama_reasoning_effort_top_level(monkeypatch):
    from app.infrastructure.model_adapter import MODEL_SPECS

    spec = next(s for s in MODEL_SPECS if s.provider == "ollama")
    captured = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="high", json_mode=True)
    assert captured["reasoning_effort"] == "high"  # Qwen3（Ollama）推理深度为顶层参数
    assert captured["response_format"] == {"type": "json_object"}  # 支持 JSON 模式


def test_ollama_uses_streaming(monkeypatch):
    """Ollama 走公网链路：必须用流式，绕过非流式长请求的链路空闲超时。"""
    from app.infrastructure.model_adapter import MODEL_SPECS

    spec = next(s for s in MODEL_SPECS if s.provider == "ollama")
    captured = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="medium", json_mode=True)
    assert captured["stream"] is True
    assert captured["reasoning_effort"] == "medium"
    assert captured["response_format"] == {"type": "json_object"}


def test_build_adapters_includes_ollama_without_key(monkeypatch):
    from app.infrastructure.model_adapter import build_adapters

    for var in ("AGNES_API_KEY", "DEEPSEEK_API_KEY", "GROK_API_KEY", "OLLAMA_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    adapters = build_adapters()
    assert "ollama" in adapters  # Ollama 通常无鉴权，始终可用


def test_check_model_availability_ollama_online(monkeypatch):
    import httpx
    from app.infrastructure.model_adapter import MODEL_SPECS, check_model_availability

    class Resp:
        status_code = 200

        def json(self):
            return {"data": [{"id": "huihui_aiQwen3.6-abliterated-27b:latest"}]}

    monkeypatch.setattr("httpx.get", lambda url, timeout: Resp())
    spec = next(s for s in MODEL_SPECS if s.provider == "ollama")
    r = check_model_availability(spec)
    assert r["available"] is True
    assert r["reason"] == "online"


def test_check_model_availability_ollama_offline(monkeypatch):
    import httpx
    from app.infrastructure.model_adapter import MODEL_SPECS, check_model_availability

    def boom(url, timeout):
        raise httpx.ConnectError("unreachable")

    monkeypatch.setattr("httpx.get", boom)
    spec = next(s for s in MODEL_SPECS if s.provider == "ollama")
    r = check_model_availability(spec)
    assert r["available"] is False
    assert r["reason"] == "ConnectError"


def test_check_model_availability_non_ollama_uses_configured(monkeypatch):
    from app.infrastructure.model_adapter import MODEL_SPECS, check_model_availability

    spec = next(s for s in MODEL_SPECS if s.provider == "deepseek")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr("app.infrastructure.config.settings.deepseek_api_key", "")
    r = check_model_availability(spec)
    assert r["available"] is False
    assert r["reason"] == "missing_api_key"


def test_fake_adapter_is_deterministic_and_records_parameters():
    adapter = FakeModelAdapter('{"candidate": "ok"}')
    assert adapter.complete([], temperature=1.1, reasoning_strength="high", json_mode=True) == '{"candidate": "ok"}'
    assert adapter.calls[0]["temperature"] == 1.1
    assert adapter.calls[0]["reasoning_strength"] == "high"
    assert adapter.calls[0]["json_mode"] is True


def test_classify_error_reveals_real_failure_cause():
    """LLM 调用失败能提取到真实原因（错误码/HTTP 状态/类别/脱敏说明）。"""
    from app.infrastructure.model_adapter import _classify_error

    def exc(name, **kw):
        cls = type(name, (Exception,), {})
        e = cls(kw.get("message", ""))
        e.status_code = kw.get("status_code")
        e.code = kw.get("code")
        e.body = kw.get("body")
        e.message = kw.get("message", "")
        return e

    # 超时
    r = _classify_error(exc("APITimeoutError", message="Request timed out."))
    assert r["error_category"] == "timeout" and r["error_type"] == "APITimeoutError"

    # 合规性拒绝（内容策略）
    r = _classify_error(exc("BadRequestError", status_code=400, code="content_filter",
                            body={"error": {"code": "content_filter", "message": "The response was filtered due to the prompt triggering the content management policy"}}))
    assert r["error_category"] == "content_policy"
    assert r["http_status"] == 400
    assert r["error_code"] == "content_filter"
    assert "content management policy" in r["error_detail"]

    # 普通参数错误（保留具体说明）
    r = _classify_error(exc("BadRequestError", status_code=400, code="invalid_request_error",
                            body={"error": {"code": "invalid_request_error", "message": "max_tokens must be <= 32768"}}))
    assert r["error_category"] == "bad_request"
    assert r["error_code"] == "invalid_request_error"
    assert "max_tokens" in r["error_detail"]

    # 限流 / 鉴权
    assert _classify_error(exc("RateLimitError", status_code=429, message="Rate limit reached"))["error_category"] == "rate_limit"
    assert _classify_error(exc("AuthenticationError", status_code=401, message="Invalid API key"))["error_category"] == "auth"

    # 未知异常：detail 回退到 str(exc)，不崩溃
    r = _classify_error(RuntimeError("boom"))
    assert r["error_detail"] == "boom"


def test_extract_json_marks_content_policy_refusal():
    """模型返回合规拒绝文本（非 JSON）时，归类为 ContentPolicyRefusalError 而非 JSONDecodeError。"""
    import pytest
    from app.infrastructure.model_adapter import ContentPolicyRefusalError, extract_json

    refusal_texts = [
        "抱歉，我无法生成此内容。请调整您的请求。",
        "对不起，我不能创作涉及敏感内容的设定。",
        "I'm sorry, but I cannot generate this content as it violates our content policy.",
        "This request has been refused due to explicit content.",
    ]
    for text in refusal_texts:
        with pytest.raises(ContentPolicyRefusalError) as excinfo:
            extract_json(text)
        assert excinfo.value.snippet  # 保留脱敏回复片段

    # 正常非 JSON 内容仍抛原始 JSONDecodeError（不误伤）
    with pytest.raises(ValueError):
        extract_json("这只是一段普通的中文叙述，没有 JSON。")


def test_classify_error_recognizes_content_policy_refusal():
    """ContentPolicyRefusalError 被归类为 content_policy，detail 为脱敏回复片段。"""
    from app.infrastructure.model_adapter import ContentPolicyRefusalError, _classify_error

    r = _classify_error(ContentPolicyRefusalError("抱歉，我无法生成此内容。"))
    assert r["error_category"] == "content_policy"
    assert r["error_type"] == "ContentPolicyRefusalError"
    assert "抱歉" in r["error_detail"]


def test_generation_failure_logs_real_cause():
    """失败生成记录包含 error_code / http_status / error_category / error_detail。"""
    import os
    from app.infrastructure import observability

    detail = "max_tokens must be <= 32768"
    observability.record_generation("__probe_action__", "__probe_model__", succeeded=False, duration_ms=12.3,
                                    error_type="BadRequestError", error_code="invalid_request_error",
                                    http_status=400, error_category="bad_request", error_detail=detail)
    log_path = os.path.join(os.environ.get("NOVEL_LOG_DIR", "logs"), "app.jsonl")
    with open(log_path, encoding="utf-8") as handle:
        last = json.loads(handle.read().strip().splitlines()[-1])
    assert last["event"] == "generation"
    assert last["status"] == "failed"
    assert last["error_category"] == "bad_request"
    assert last["http_status"] == 400
    assert last["error_code"] == "invalid_request_error"
    assert last["error_detail"] == detail


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


# ---------------------------------------------------------------------------
# 系统提示词集中管理（app/infrastructure/prompts.py）
# ---------------------------------------------------------------------------

ALL_GENERATION_ACTIONS = {
    "generate_concept", "generate_title", "generate_blueprint", "generate_chapter_plan",
    "generate_scene_plan", "generate_beat_plan", "generate_scene", "scene_summary",
    "extract_delta", "consistency_check", "review_blueprint_updates",
}


def test_prompts_module_covers_all_actions_and_versions():
    """所有生成任务在 prompts.py 中都有系统提示词与版本号。"""
    from app.infrastructure.prompts import PROMPT_VERSIONS, SYSTEM_PROMPTS, prompt_version, system_prompt

    assert set(SYSTEM_PROMPTS) == set(PROMPT_VERSIONS)
    assert set(SYSTEM_PROMPTS) == ALL_GENERATION_ACTIONS
    for action in SYSTEM_PROMPTS:
        assert system_prompt(action).strip(), f"{action} 缺少系统提示词"
        assert prompt_version(action) >= 1, f"{action} 缺少提示词版本号"
    # 未知 action 回退通用提示，不中断生成。
    assert system_prompt("unknown_action").startswith("你是一个")
    assert prompt_version("unknown_action") == 1


def test_generation_task_records_prompt_version(client, monkeypatch, tmp_path):
    """每次生成在 generation_tasks 记录所用提示词版本（prompt_version）。"""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.infrastructure.prompts import prompt_version

    monkeypatch.setattr("app.works.concept_service.build_adapters", lambda: {})
    created = client.post("/api/v1/works", json={"title": "提示词版本"}).json()
    story_id = created["id"]
    client.put(f"/api/v1/stories/{story_id}/idea", json={"idea_text": "一位能听见墙壁心跳的人。", "expected_version": created["version"]})
    client.post(f"/api/v1/stories/{story_id}/generations", json={"action": "generate_concept"})

    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as db:
        row = db.execute(
            text("SELECT action, prompt_version, status FROM generation_tasks WHERE story_id = :sid ORDER BY created_at DESC LIMIT 1").bindparams(sid=story_id)
        ).first()
        assert row is not None
        assert row.action == "generate_concept"
        assert row.prompt_version == prompt_version("generate_concept") >= 1
        assert row.status == "succeeded"


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
