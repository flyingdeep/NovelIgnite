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
    assert {model["provider"] for model in models} == {"agnes", "deepseek", "grok", "llamacpp"}
    assert next(model for model in models if model["provider"] == "grok")["supports_json"] is False
    assert next(model for model in models if model["provider"] == "llamacpp")["supports_json"] is True


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
    assert limits["llamacpp"] == 32768  # llama.cpp：服务器 16K ctx 未设输出上限，设大值备复杂长文（服务器自动压缩到 n_ctx - prompt）


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


def test_llamacpp_spec_registered():
    from app.infrastructure.model_adapter import MODEL_SPECS

    llamacpp = next(spec for spec in MODEL_SPECS if spec.provider == "llamacpp")
    assert llamacpp.name == "Qwen3.6 35B A3B (llama.cpp)"
    assert llamacpp.model == "qwen3.6-35b-a3b"
    assert llamacpp.base_url == "http://106.75.216.144:57321/v1"
    assert llamacpp.supports_json is True
    assert llamacpp.thinking == "llamacpp"
    assert llamacpp.max_output_tokens == 32768


def test_llamacpp_thinking_params(monkeypatch):
    from app.infrastructure.model_adapter import MODEL_SPECS

    spec = next(s for s in MODEL_SPECS if s.provider == "llamacpp")
    captured = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="high", json_mode=True)
    assert captured["extra_body"]["chat_template_kwargs"] == {"enable_thinking": True}  # Qwen3.6（llama.cpp）思考经 chat_template_kwargs 控制
    assert captured["response_format"] == {"type": "json_object"}  # 支持 JSON 模式
    captured_low = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="low")
    assert captured_low["extra_body"]["chat_template_kwargs"] == {"enable_thinking": False}  # low 视为关闭思考


def test_llamacpp_uses_streaming(monkeypatch):
    """llama.cpp 走公网链路：必须用流式，绕过非流式长请求的链路空闲超时。"""
    from app.infrastructure.model_adapter import MODEL_SPECS

    spec = next(s for s in MODEL_SPECS if s.provider == "llamacpp")
    captured = _capture_adapter_kwargs(monkeypatch, spec, reasoning_strength="medium", json_mode=True)
    assert captured["stream"] is True
    assert captured["response_format"] == {"type": "json_object"}


def test_build_adapters_includes_llamacpp_without_key(monkeypatch):
    from app.infrastructure.model_adapter import build_adapters

    for var in ("AGNES_API_KEY", "DEEPSEEK_API_KEY", "GROK_API_KEY", "LLAMACPP_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    adapters = build_adapters()
    assert "llamacpp" in adapters  # llama.cpp 通常无鉴权，始终可用


def test_check_model_availability_llamacpp_online(monkeypatch):
    import httpx
    from app.infrastructure.model_adapter import MODEL_SPECS, check_model_availability

    class Resp:
        status_code = 200

        def json(self):
            return {"data": [{"id": "qwen3.6-35b-a3b"}]}

    monkeypatch.setattr("httpx.get", lambda url, timeout: Resp())
    spec = next(s for s in MODEL_SPECS if s.provider == "llamacpp")
    r = check_model_availability(spec)
    assert r["available"] is True
    assert r["reason"] == "online"


def test_check_model_availability_llamacpp_offline(monkeypatch):
    import httpx
    from app.infrastructure.model_adapter import MODEL_SPECS, check_model_availability

    def boom(url, timeout):
        raise httpx.ConnectError("unreachable")

    monkeypatch.setattr("httpx.get", boom)
    spec = next(s for s in MODEL_SPECS if s.provider == "llamacpp")
    r = check_model_availability(spec)
    assert r["available"] is False
    assert r["reason"] == "ConnectError"


def test_check_model_availability_non_llamacpp_uses_configured(monkeypatch):
    from app.infrastructure.model_adapter import MODEL_SPECS, check_model_availability

    spec = next(s for s in MODEL_SPECS if s.provider == "deepseek")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr("app.infrastructure.config.settings.deepseek_api_key", "")
    r = check_model_availability(spec)
    assert r["available"] is False
    assert r["reason"] == "missing_api_key"


def test_is_retryable_marks_transient_errors():
    """瞬时错误（连接/超时/5xx/限流）可重试；参数错误/鉴权/合规拒绝不重试。"""
    from app.infrastructure.model_adapter import _is_retryable

    def make(name):
        return type(name, (Exception,), {})("x")

    assert _is_retryable(make("APIConnectionError"))
    assert _is_retryable(make("APITimeoutError"))
    assert _is_retryable(make("ReadTimeout"))
    assert _is_retryable(make("InternalServerError"))
    assert _is_retryable(make("RateLimitError"))
    assert not _is_retryable(make("BadRequestError"))
    assert not _is_retryable(make("AuthenticationError"))
    assert not _is_retryable(make("ContentPolicyRefusalError"))


def test_complete_retries_transient_connection_error(monkeypatch):
    """连接类瞬时错误自动重试后成功返回。"""
    from app.infrastructure.model_adapter import MODEL_SPECS, OpenAICompatibleAdapter

    spec = next(s for s in MODEL_SPECS if s.provider == "deepseek")
    calls = {"n": 0}

    class FlakyCompletions:
        def create(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise type("APIConnectionError", (Exception,), {})("Connection error.")
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "ok"})()})()], "usage": None})()

    class FlakyClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FlakyCompletions()})()

    monkeypatch.setenv(spec.api_key_env, "test")
    monkeypatch.setattr("openai.OpenAI", FlakyClient)
    text = OpenAICompatibleAdapter(spec).complete([{"role": "user", "content": "hi"}], action="__retry_test__")
    assert text == "ok"
    assert calls["n"] == 2  # 失败 1 次后重试成功


def test_complete_does_not_retry_bad_request(monkeypatch):
    """参数错误/非瞬时错误不重试（避免掩盖真实失败原因）。"""
    import pytest
    from app.infrastructure.model_adapter import MODEL_SPECS, OpenAICompatibleAdapter

    spec = next(s for s in MODEL_SPECS if s.provider == "deepseek")
    calls = {"n": 0}

    class BadCompletions:
        def create(self, **kwargs):
            calls["n"] += 1
            raise type("BadRequestError", (Exception,), {})("max_tokens must be <= 32768")

    class BadClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": BadCompletions()})()

    monkeypatch.setenv(spec.api_key_env, "test")
    monkeypatch.setattr("openai.OpenAI", BadClient)
    with pytest.raises(Exception):
        OpenAICompatibleAdapter(spec).complete([{"role": "user", "content": "hi"}])
    assert calls["n"] == 1


def test_model_prompt_profile_persists_and_stacks_with_task_prompt(client):
    """模型预设提示词落库，并与任务提示词叠加而非覆盖。"""
    provider = "deepseek"
    listed = client.get("/api/v1/models/prompt-profiles")
    assert listed.status_code == 200
    initial = next(item for item in listed.json() if item["provider"] == provider)
    assert initial["version"] == 0

    saved = client.put(f"/api/v1/models/{provider}/prompt-profile", json={
        "system_prompt": "请使用大众易懂、通顺的中文表达，保持自然过渡。",
        "expected_version": 0,
    })
    assert saved.status_code == 200
    assert saved.json()["version"] == 1

    # 重新读取仍在：真实服务重启后 SQLite 的同一记录也会保留。
    again = client.get("/api/v1/models/prompt-profiles").json()
    profile = next(item for item in again if item["provider"] == provider)
    assert profile["system_prompt"].startswith("请使用大众易懂")
    assert profile["version"] == 1

    from app.infrastructure.database import get_db
    from app.infrastructure.model_prompt_profiles import compose_system_prompt

    # client 的 override session 中直接验证最终系统提示词含两个独立层。
    db = next(iter(client.app.dependency_overrides[get_db]()))
    try:
        composed = compose_system_prompt(db, provider, "generate_scene")
        assert "模型预设系统提示词" in composed
        assert "大众易懂" in composed
        assert "当前任务系统提示词" in composed
        assert "当前节拍" in composed  # 任务提示词的任务边界仍然存在
    finally:
        db.close()


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


def test_normalize_blueprint_fields_from_string_and_array():
    """模型把 fields 输出成字符串或二维数组时，必须被规范化为 {label: value}，不得逐字拆散。"""
    from app.works.blueprint_service import normalize_blueprint_payload

    raw = {
        "characters": {"title": "人物", "entries": [{
            "name": "林晚晴",
            "role": "主角/特警突击手",
            "fields": "性格冷峻果决、体能反应顶尖；职业身份为市局特警支队骨干；动机是完成斩断贩卖链的誓言；缺陷是过度依赖理智与控制欲；初始关系为独立执行任务。",
        }]},
        "world": {"title": "世界", "entries": [{"name": "岛屿", "role": "主舞台", "fields": [["description", "离岸管制岛屿"], ["rules", "禁航区"]]}]},
        "timeline": {"title": "初始时间线", "entries": [{"name": "开场", "role": "初始状态", "fields": {"before_story": "三年前行动失败"}}]},
        "arc": {"title": "故事弧", "entries": [{"name": "主线", "role": "方向", "fields": {"premise": "斩断贩卖链"}}]},
    }
    payload, fallback_used = normalize_blueprint_payload(raw, "孤岛卧底", {})
    assert fallback_used is False
    char_fields = payload["characters"]["entries"][0]["fields"]
    assert isinstance(char_fields, dict)
    # 字符串被正确切分，而不是整个塞进一个字段或逐字拆散。
    assert "性格" in char_fields and "冷峻果决、体能反应顶尖" in char_fields["性格"]
    assert char_fields["职业身份"] == "市局特警支队骨干"
    assert char_fields["动机"].startswith("完成斩断贩卖链")
    assert "缺陷" in char_fields and "初始关系" in char_fields
    # 二维数组被转成字典；对象保持不变。
    assert payload["world"]["entries"][0]["fields"] == {"description": "离岸管制岛屿", "rules": "禁航区"}
    assert payload["timeline"]["entries"][0]["fields"] == {"before_story": "三年前行动失败"}


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
    "readability_review", "extract_delta", "consistency_check", "review_blueprint_updates",
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


def test_concept_prompt_preserves_author_intent():
    """概念生成提示词必须约束模型完整保留作者已提供的细节，不得删减/简化/改写。"""
    from app.infrastructure.prompts import system_prompt

    concept = system_prompt("generate_concept")
    assert "作者意图保留" in concept
    assert "最高优先" in concept
    assert "禁止删减" in concept and "简化" in concept and "改写" in concept
    # summary 必须完整覆盖作者已写细节，不能概括丢弃。
    assert "不删减" in concept and "不简写" in concept


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
