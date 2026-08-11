"""OpenAI-compatible model adapter contract and provider registry."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

from app.infrastructure.config import settings


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    name: str
    model: str
    base_url: str
    api_key_env: str
    supports_json: bool


MODEL_SPECS = (
    ModelSpec("agnes", "Agnes 2.0 Flash", "agnes-2.0-flash", "https://apihub.agnes-ai.com/v1", "AGNES_API_KEY", True),
    ModelSpec("deepseek", "DeepSeek V4 Flash", "deepseek-v4-flash", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", True),
    ModelSpec("grok", "Grok 4.5", "grok-4.5", "https://modelflare.dev/v1", "GROK_API_KEY", False),
)


class ModelAdapter(Protocol):
    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.7, reasoning_strength: str = "medium", json_mode: bool = False, max_tokens: int = 4096) -> str: ...


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

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.7, reasoning_strength: str = "medium", json_mode: bool = False, max_tokens: int = 4096) -> str:
        from openai import OpenAI

        api_key = os.getenv(self.spec.api_key_env) or getattr(settings, self.spec.api_key_env.lower(), "")
        if not api_key:
            raise RuntimeError(f"Missing model API key: {self.spec.api_key_env}")
        client = OpenAI(base_url=self.spec.base_url, api_key=api_key, timeout=self.timeout)
        kwargs: dict[str, Any] = {
            "model": self.spec.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if reasoning_strength in {"low", "medium", "high"}:
            kwargs["extra_body"] = {"reasoning_effort": reasoning_strength}
        if json_mode and self.spec.supports_json:
            kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""


def configured_model_specs() -> list[ModelSpec]:
    return list(MODEL_SPECS)


def build_adapters(timeout: float = 180) -> dict[str, OpenAICompatibleAdapter]:
    return {
        spec.provider: OpenAICompatibleAdapter(spec, timeout=timeout)
        for spec in MODEL_SPECS
        if os.getenv(spec.api_key_env) or getattr(settings, spec.api_key_env.lower(), "")
    }
