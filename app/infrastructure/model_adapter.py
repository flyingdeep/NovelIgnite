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


# 模型拒绝生成时常见的中文/英文表达（用于把「返回非 JSON 的拒绝文本」归类为内容策略拒绝）。
_REFUSAL_HINTS = (
    "抱歉", "无法生成", "无法满足", "无法创作", "无法完成", "不能生成", "不能创作", "无法提供", "无法处理",
    "不予", "拒绝", "不适合", "不允许", "敏感内容", "成人内容", "内容政策", "内容策略", "安全审查",
    "违反", "违反政策", "合规要求", "sorry", "cannot generate", "can't generate", "cannot create",
    "not able to", "not allowed", "unable to", "refus", "decline", "content policy",
    "content filter", "moderation", "inappropriate", "explicit", "unsafe", "harmful",
)


class ContentPolicyRefusalError(ValueError):
    """模型返回了合规性拒绝文本（非 JSON），用于可观测性归类。

    与 JSONDecodeError 不同，此类异常表明失败真实原因是模型安全/内容策略拒绝，
    而非输出格式错误；snippet 保存脱敏后的回复开头以便排查。
    """

    def __init__(self, snippet: str):
        self.snippet = snippet
        super().__init__("Model returned a content-policy refusal instead of JSON")


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
        # 解析失败：若原始回复是明显的合规性拒绝文本，归类为内容策略拒绝而非格式错误
        low = cleaned.lower()
        if any(h in low for h in _REFUSAL_HINTS):
            snippet = "".join(ch for ch in cleaned if ch.isprintable()).strip()[:200]
            raise ContentPolicyRefusalError(snippet) from None
        raise


# 合规性拒绝/内容策略关键词（用于把 400 类错误归类为内容策略拒绝）。
_CONTENT_POLICY_HINTS = ("content_filter", "content policy", "moderation", "refusal", "safety", "policy violation", "合规", "内容策略", "安全审查")


def _classify_error(exc: Exception) -> dict[str, Any]:
    """从模型 API 异常提取安全的失败原因，供可观测性记录。

    返回 {error_type, error_code, http_status, error_category, error_detail}：
    - error_type: 异常类名（如 BadRequestError / APITimeoutError）
    - error_code: 提供商返回的错误码（body.error.code）
    - http_status: HTTP 状态码（400/401/429/500...）
    - error_category: 归类（timeout/connection/auth/rate_limit/content_policy/bad_request/...）
    - error_detail: 脱敏、截断后的失败说明（仅 API 返回的错误信息，不含 prompt/正文/密钥）
    """
    error_type = type(exc).__name__
    status = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    detail: str | None = None
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            code = code or err.get("code")
            msg = err.get("message")
            if msg:
                detail = str(msg)
        elif body.get("message"):
            detail = str(body["message"])
    if not detail:
        raw = getattr(exc, "message", None)
        if raw:
            detail = str(raw)
    if not detail:
        detail = str(exc) or None
    if detail:
        detail = "".join(ch for ch in detail if ch.isprintable()).strip()
        detail = detail[:300]

    category = "other"
    if isinstance(exc, ContentPolicyRefusalError):
        category = "content_policy"
        # snippet（脱敏回复片段）比默认消息更能说明真实原因，直接覆盖 detail
        detail = exc.snippet or "Model returned a content-policy refusal instead of JSON"
        detail = "".join(ch for ch in detail if ch.isprintable()).strip()[:300]
    elif error_type in ("APITimeoutError", "Timeout", "ReadTimeout", "ConnectTimeout"):
        category = "timeout"
    elif error_type in ("APIConnectionError", "ConnectionError", "ConnectError"):
        category = "connection"
    elif error_type == "AuthenticationError":
        category = "auth"
    elif error_type == "PermissionDeniedError":
        category = "permission"
    elif error_type == "RateLimitError":
        category = "rate_limit"
    elif error_type in ("NotFoundError",):
        category = "not_found"
    elif error_type in ("InternalServerError",):
        category = "server"
    elif error_type in ("BadRequestError", "UnprocessableEntityError"):
        low = (detail or "").lower()
        code_low = str(code or "").lower()
        if code_low in ("content_filter", "safety", "policy") or any(h in low for h in _CONTENT_POLICY_HINTS):
            category = "content_policy"
        else:
            category = "bad_request"
    elif error_type.endswith("Error") or error_type.endswith("Exception"):
        category = "api"
    return {
        "error_type": error_type,
        "error_code": code,
        "http_status": status,
        "error_category": category,
        "error_detail": detail,
    }



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
            record_generation(action, self.spec.provider, succeeded=False, duration_ms=duration_ms, **_classify_error(exc))
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
