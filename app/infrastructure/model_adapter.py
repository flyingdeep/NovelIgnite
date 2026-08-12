"""OpenAI-compatible model adapter contract and provider registry."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

from app.infrastructure.config import settings
from app.infrastructure.observability import record_generation


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    name: str
    model: str
    base_url: str
    api_key_env: str
    supports_json: bool
    # 推理/思考参数如何传递（依据各模型官方文档）：
    #   "deepseek": extra_body.thinking={type:enabled} + 顶层 reasoning_effort(low/high/max)；medium 映射为 high
    #   "agnes":    extra_body.chat_template_kwargs={enable_thinking: true/false}
    #   "grok":     顶层 reasoning_effort(low/medium/high)，推理无法关闭
    thinking: str = "builtin"
    # 官方允许的最大输出 tokens（DeepSeek 384K / Agnes 2.5 65.5K / Grok 4.5 500K）
    max_output_tokens: int = 4096


MODEL_SPECS = (
    ModelSpec("agnes", "Agnes 2.5 Flash", "agnes-2.5-flash", "https://apihub.agnes-ai.com/v1", "AGNES_API_KEY", True, "agnes", 65536),
    ModelSpec("deepseek", "DeepSeek V4 Flash", "deepseek-v4-flash", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", True, "deepseek", 384000),
    ModelSpec("grok", "Grok 4.5", "grok-4.5", "https://modelflare.dev/v1", "GROK_API_KEY", False, "grok", 500000),
)


class ModelAdapter(Protocol):
    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.7, reasoning_strength: str = "medium", json_mode: bool = False, max_tokens: int | None = None, action: str = "chat") -> str: ...


def extract_json(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


class OpenAICompatibleAdapter:
    def __init__(self, spec: ModelSpec, *, timeout: float = 180):
        self.spec = spec
        self.timeout = timeout

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.7, reasoning_strength: str = "medium", json_mode: bool = False, max_tokens: int | None = None, action: str = "chat") -> str:
        from openai import OpenAI

        api_key = os.getenv(self.spec.api_key_env) or getattr(settings, self.spec.api_key_env.lower(), "")
        if not api_key:
            raise RuntimeError(f"Missing model API key: {self.spec.api_key_env}")
        if max_tokens is None:
            max_tokens = self.spec.max_output_tokens
        client = OpenAI(base_url=self.spec.base_url, api_key=api_key, timeout=self.timeout)
        kwargs: dict[str, Any] = {
            "model": self.spec.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        extra_body: dict[str, Any] = {}
        if self.spec.thinking == "deepseek":
            # DeepSeek 思考模式默认开启；显式开启并按官方映射表映射强度（low→low，medium/high→high，max→max）
            extra_body["thinking"] = {"type": "enabled"}
            kwargs["reasoning_effort"] = {"low": "low", "medium": "high", "high": "high"}.get(reasoning_strength, "high")
        elif self.spec.thinking == "agnes":
            # Agnes 2.5 Flash：通过 chat_template_kwargs.enable_thinking 开启思考；low 视为关闭思考
            extra_body["chat_template_kwargs"] = {"enable_thinking": reasoning_strength != "low"}
        elif self.spec.thinking == "grok":
            # Grok 4.5：推理无法关闭，reasoning_effort 为顶层参数（low/medium/high）
            kwargs["reasoning_effort"] = reasoning_strength
        if extra_body:
            kwargs["extra_body"] = extra_body
        if json_mode and self.spec.supports_json:
            kwargs["response_format"] = {"type": "json_object"}
        start = time.perf_counter()
        try:
            response = client.chat.completions.create(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            usage = getattr(response, "usage", None)
            tokens = None
            if usage is not None:
                tokens = {
                    "prompt": getattr(usage, "prompt_tokens", None),
                    "completion": getattr(usage, "completion_tokens", None),
                    "total": getattr(usage, "total_tokens", None),
                }
            record_generation(action, self.spec.provider, succeeded=True, duration_ms=duration_ms, tokens=tokens)
            return response.choices[0].message.content or ""
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            record_generation(action, self.spec.provider, succeeded=False, duration_ms=duration_ms, error_type=type(exc).__name__)
            raise


def configured_model_specs() -> list[ModelSpec]:
    return list(MODEL_SPECS)


def build_adapters(timeout: float | None = None) -> dict[str, OpenAICompatibleAdapter]:
    if timeout is None:
        timeout = settings.model_timeout
    return {
        spec.provider: OpenAICompatibleAdapter(spec, timeout=timeout)
        for spec in MODEL_SPECS
        if os.getenv(spec.api_key_env) or getattr(settings, spec.api_key_env.lower(), "")
    }
