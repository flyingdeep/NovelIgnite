"""Lightweight observability: structured JSONL logs + in-memory metrics.

Privacy rules (see .github/copilot-instructions.md):
- Never logs full prompts, generated prose, or API keys.
- Generation events record model, action, latency, token usage, and error type only.
- Metrics live in memory (reset on restart); the JSONL file in `logs/` is the durable
  record for offline analysis and is excluded from Git.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(os.getenv("NOVEL_LOG_DIR", "logs"))
_LOG_FILE = LOG_DIR / "app.jsonl"
_RECENT_LIMIT = 300
# 日志轮转：单文件超过该字节数即滚动为 app.jsonl.1/.2/...，保留最近 N 份
_MAX_LOG_BYTES = int(os.getenv("NOVEL_MAX_LOG_BYTES", str(5 * 1024 * 1024)))
_MAX_LOG_BACKUPS = 5

_lock = threading.Lock()
_metrics = {
    "started_at": time.time(),
    "requests": {"total": 0, "by_status": {}},
    "generations": {"total": 0, "succeeded": 0, "failed": 0, "ms_total": 0.0, "max_ms": 0.0, "by_action": {}, "by_model": {}},
    "errors": {},
    "error_categories": {},
}
_recent: list[dict] = []


def _ensure_dir() -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _rotate_if_needed() -> None:
    """Roll the log file when it exceeds the size cap (best-effort, never raises)."""
    try:
        if not _LOG_FILE.exists() or _LOG_FILE.stat().st_size < _MAX_LOG_BYTES:
            return
        for i in range(_MAX_LOG_BACKUPS - 1, 0, -1):
            src = Path(f"{_LOG_FILE}.{i}")
            dst = Path(f"{_LOG_FILE}.{i + 1}")
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        _LOG_FILE.rename(Path(f"{_LOG_FILE}.1"))
    except Exception:
        pass


def _write(payload: dict) -> None:
    _ensure_dir()
    _rotate_if_needed()
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _append_recent(payload: dict) -> None:
    with _lock:
        _recent.append(payload)
        if len(_recent) > _RECENT_LIMIT:
            del _recent[: len(_recent) - _RECENT_LIMIT]


def log_event(event: str, **fields: object) -> None:
    """Write one structured event line (JSON) to the log file and recent buffer."""
    payload = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    _append_recent(payload)
    _write(payload)


def record_request(method: str, path: str, status: int, duration_ms: float) -> None:
    """Record one HTTP request (method, path, status, latency)."""
    with _lock:
        _metrics["requests"]["total"] += 1
        key = str(status)
        _metrics["requests"]["by_status"][key] = _metrics["requests"]["by_status"].get(key, 0) + 1
    log_event("request", method=method, path=path, status=status, ms=round(duration_ms, 1))


def _bump(counter: dict, key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _accumulate(counter: dict, key: str, duration_ms: float) -> None:
    bucket = counter.setdefault(key, {"total": 0, "succeeded": 0, "failed": 0, "ms_total": 0.0, "max_ms": 0.0})
    bucket["total"] += 1
    bucket["ms_total"] += duration_ms
    bucket["max_ms"] = max(bucket["max_ms"], duration_ms)
    return bucket


def record_generation(action: str, model: str, *, succeeded: bool, duration_ms: float, tokens: dict | None = None, error_type: str | None = None, error_code: str | None = None, http_status: int | None = None, error_category: str | None = None, error_detail: str | None = None) -> None:
    """Record one model generation call (the core signal for LLM analysis).

    On failure, error_type (exception class), error_code (provider error code),
    http_status, error_category (timeout/content_policy/rate_limit/...) and a
    truncated, sanitized error_detail are recorded so the real cause is traceable.
    """
    with _lock:
        m = _metrics["generations"]
        m["total"] += 1
        m["ms_total"] += duration_ms
        m["max_ms"] = max(m["max_ms"], duration_ms)
        if succeeded:
            m["succeeded"] += 1
        else:
            m["failed"] += 1
            if error_type:
                _bump(_metrics["errors"], error_type)
            if error_category:
                _bump(_metrics["error_categories"], error_category)
        act = _accumulate(m["by_action"], action, duration_ms)
        mod = _accumulate(m["by_model"], model, duration_ms)
        if succeeded:
            act["succeeded"] += 1
            mod["succeeded"] += 1
        else:
            act["failed"] += 1
            mod["failed"] += 1
    log_event(
        "generation",
        action=action,
        model=model,
        status="succeeded" if succeeded else "failed",
        ms=round(duration_ms, 1),
        tokens=tokens,
        error_type=error_type,
        error_code=error_code,
        http_status=http_status,
        error_category=error_category,
        error_detail=error_detail,
    )


def _summarize(counter: dict) -> dict:
    out: dict = {}
    for key, bucket in counter.items():
        out[key] = {
            "total": bucket["total"],
            "succeeded": bucket["succeeded"],
            "failed": bucket["failed"],
            "avg_ms": round(bucket["ms_total"] / bucket["total"], 1) if bucket["total"] else 0,
            "max_ms": round(bucket["max_ms"], 1),
        }
    return out


def snapshot() -> dict:
    """Return a JSON-serializable metrics snapshot for the /metrics endpoint."""
    with _lock:
        m = _metrics["generations"]
        return {
            "started_at": _metrics["started_at"],
            "uptime_seconds": round(time.time() - _metrics["started_at"], 1),
            "requests": {
                "total": _metrics["requests"]["total"],
                "by_status": dict(_metrics["requests"]["by_status"]),
            },
            "generations": {
                "total": m["total"],
                "succeeded": m["succeeded"],
                "failed": m["failed"],
                "success_rate": round(m["succeeded"] / m["total"], 4) if m["total"] else 0,
                "avg_ms": round(m["ms_total"] / m["total"], 1) if m["total"] else 0,
                "max_ms": round(m["max_ms"], 1),
                "by_action": _summarize(m["by_action"]),
                "by_model": _summarize(m["by_model"]),
            },
            "errors": dict(_metrics["errors"]),
            "error_categories": dict(_metrics["error_categories"]),
            "recent_events": list(_recent[-50:]),
        }
