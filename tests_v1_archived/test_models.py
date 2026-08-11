from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.config import Settings
from app.infrastructure.database import Base
from app.projects.service import (
    ModelSpec,
    OpenAICompatibleModelAdapter,
    ProjectService,
    _extract_json,
    build_model_adapters,
)


def make_settings(**overrides):
    base = {
        "agnes_api_key": "agnes-key",
        "deepseek_api_key": "deepseek-key",
        "grok_api_key": "grok-key",
    }
    base.update(overrides)
    return Settings(**base)


def test_build_model_adapters_includes_configured_providers():
    adapters = build_model_adapters(make_settings())
    assert set(adapters) == {"fake", "agnes", "deepseek", "grok"}


def test_build_model_adapters_skips_provider_without_key():
    adapters = build_model_adapters(make_settings(grok_api_key=None))
    assert "grok" not in adapters
    assert "fake" in adapters


def test_grok_omits_response_format_while_others_include_it():
    for provider, supports in (("agnes", True), ("deepseek", True), ("grok", False)):
        adapter = OpenAICompatibleModelAdapter(
            ModelSpec(provider, provider, "https://example.com/v1", "key", "model-name", supports, 30)
        )
        with patch("app.projects.service.httpx.post") as post:
            post.return_value.status_code = 200
            post.return_value.raise_for_status = lambda: None
            post.return_value.json.return_value = {"choices": [{"message": {"content": '{"genre": "科幻"}'}}]}
            adapter.generate_concept("我的创意", {})
        body = post.call_args.kwargs["json"]
        assert ("response_format" in body) is supports
        assert body["model"] == "model-name"
        assert body["messages"][1]["content"] == "我的创意"
        assert "provider" not in body
        assert "api_key" not in body


def test_extract_json_handles_markdown_and_surrounding_text():
    assert _extract_json({"genre": "科幻"}) == {"genre": "科幻"}
    wrapped = '```json\n{"genre": "科幻"}\n```'
    assert _extract_json(wrapped) == {"genre": "科幻"}
    mixed = '好的，以下是结果：{"genre": "科幻"} 请查收。'
    assert _extract_json(mixed) == {"genre": "科幻"}


def test_project_service_supports_provider_override_and_records_snapshot():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()

    service = ProjectService(
        session,
        models=build_model_adapters(make_settings()),
        default_provider="fake",
    )
    story = service.create_story("测试创意", "测试")
    with patch("app.projects.service.httpx.post") as post:
        post.return_value.status_code = 200
        post.return_value.raise_for_status = lambda: None
        post.return_value.json.return_value = {"choices": [{"message": {"content": '{"genre": "科幻"}'}}]}
        task = service.generate_concept(story.id, {"provider": "deepseek"})
    assert task.status == "succeeded"
    assert task.model_snapshot["provider"] == "deepseek"
    assert "key" not in str(task.model_snapshot)
    assert "response_format" in post.call_args.kwargs["json"]
