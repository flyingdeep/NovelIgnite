"""分析 logs/app.jsonl 生成运行报表（面向大模型性能优化与问题排除）。

用法：
    py -3.13 scripts/analyze_metrics.py                # 终端汇总报表
    py -3.13 scripts/analyze_metrics.py --json         # 输出结构化 JSON（便于程序化分析）
    py -3.13 scripts/analyze_metrics.py --log 日志路径 --top-slow 10

说明：仅读取日志，不写库；日志不包含完整提示词/正文/密钥。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_LOG = Path(__file__).resolve().parents[1] / "logs" / "app.jsonl"


def load_events(path: Path) -> list[dict]:
    events: list[dict] = []
    if not path.exists():
        print(f"[warn] 日志不存在: {path}", file=sys.stderr)
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _round(value: float) -> float:
    return round(value, 1)


def summarize(events: list[dict]) -> dict:
    requests = [e for e in events if e.get("event") == "request"]
    generations = [e for e in events if e.get("event") == "generation"]
    request_errors = [e for e in events if e.get("event") == "request_error"]

    req_by_status: dict[str, int] = defaultdict(int)
    req_times = [e.get("ms", 0) for e in requests]
    slow_requests = sorted(requests, key=lambda e: e.get("ms", 0), reverse=True)[:10]

    gen_by_action: dict[str, dict] = {}
    gen_by_model: dict[str, dict] = {}
    errors: dict[str, int] = defaultdict(int)
    slow_generations = sorted(generations, key=lambda e: e.get("ms", 0), reverse=True)[:10]
    token_total = {"prompt": 0, "completion": 0, "total": 0}

    for e in generations:
        status = e.get("status", "?")
        ms = e.get("ms", 0)
        action = e.get("action", "?")
        model = e.get("model", "?")
        for bucket in (gen_by_action.setdefault(action, {"total": 0, "succeeded": 0, "failed": 0, "ms_total": 0.0, "max_ms": 0.0, "tokens": 0}),
                       gen_by_model.setdefault(model, {"total": 0, "succeeded": 0, "failed": 0, "ms_total": 0.0, "max_ms": 0.0, "tokens": 0})):
            bucket["total"] += 1
            bucket["ms_total"] += ms
            bucket["max_ms"] = max(bucket["max_ms"], ms)
            if status == "succeeded":
                bucket["succeeded"] += 1
            else:
                bucket["failed"] += 1
        if e.get("status") != "succeeded" and e.get("error_type"):
            errors[e["error_type"]] += 1
        tokens = e.get("tokens") or {}
        token_total["prompt"] += tokens.get("prompt") or 0
        token_total["completion"] += tokens.get("completion") or 0
        token_total["total"] += tokens.get("total") or 0
        for b in (gen_by_action[action], gen_by_model[model]):
            b["tokens"] += tokens.get("total") or 0

    for e in requests:
        req_by_status[str(e.get("status", 0))] += 1

    def _finalize(bucket: dict) -> dict:
        total = bucket["total"] or 1
        return {
            "total": bucket["total"],
            "succeeded": bucket["succeeded"],
            "failed": bucket["failed"],
            "success_rate": round(bucket["succeeded"] / total, 4),
            "avg_ms": _round(bucket["ms_total"] / total) if bucket["total"] else 0,
            "max_ms": _round(bucket["max_ms"]),
            "tokens": bucket["tokens"],
        }

    return {
        "overview": {
            "events": len(events),
            "requests": len(requests),
            "generations": len(generations),
            "request_errors": len(request_errors),
            "first_ts": events[0].get("ts") if events else None,
            "last_ts": events[-1].get("ts") if events else None,
        },
        "requests": {
            "total": len(requests),
            "by_status": dict(sorted(req_by_status.items())),
            "avg_ms": _round(sum(req_times) / len(req_times)) if req_times else 0,
            "max_ms": _round(max(req_times)) if req_times else 0,
            "slowest": [{"method": e.get("method"), "path": e.get("path"), "status": e.get("status"), "ms": e.get("ms"), "ts": e.get("ts")} for e in slow_requests],
        },
        "generations": {
            "total": len(generations),
            "succeeded": sum(1 for e in generations if e.get("status") == "succeeded"),
            "failed": sum(1 for e in generations if e.get("status") == "failed"),
            "by_action": {k: _finalize(v) for k, v in sorted(gen_by_action.items())},
            "by_model": {k: _finalize(v) for k, v in sorted(gen_by_model.items())},
            "tokens": token_total,
            "slowest": [{"action": e.get("action"), "model": e.get("model"), "status": e.get("status"), "ms": e.get("ms"), "error_type": e.get("error_type"), "ts": e.get("ts")} for e in slow_generations],
        },
        "errors": dict(sorted(errors.items(), key=lambda item: -item[1])),
    }


def print_report(report: dict) -> None:
    ov = report["overview"]
    print("=" * 72)
    print("Novel Ignite 运行报表")
    print("=" * 72)
    print(f"事件总数: {ov['events']} | 请求: {ov['requests']} | 生成调用: {ov['generations']} | 请求异常: {ov['request_errors']}")
    print(f"时间范围: {ov['first_ts']} -> {ov['last_ts']}")

    print("\n-- 请求 --")
    req = report["requests"]
    print(f"总数 {req['total']} | 平均 {req['avg_ms']}ms | 最大 {req['max_ms']}ms")
    print("状态码分布: " + ", ".join(f"{k}: {v}" for k, v in req["by_status"].items()))
    if req["slowest"]:
        print("最慢请求:")
        for item in req["slowest"]:
            print(f"  {item['ms']:>8.1f}ms  {item['method']} {item['path']}  [{item['status']}]  {item['ts']}")

    print("\n-- 生成调用（按 action）--")
    _print_gen_table(report["generations"]["by_action"])
    print("\n-- 生成调用（按模型）--")
    _print_gen_table(report["generations"]["by_model"])
    gens = report["generations"]
    print(f"\nToken 合计: prompt={gens['tokens']['prompt']} completion={gens['tokens']['completion']} total={gens['tokens']['total']}")
    if gens["slowest"]:
        print("最慢生成:")
        for item in gens["slowest"]:
            print(f"  {item['ms']:>8.1f}ms  {item['action']} / {item['model']}  [{item['status']} {item.get('error_type') or ''}]  {item['ts']}")

    print("\n-- 错误类型 --")
    if report["errors"]:
        for name, count in report["errors"].items():
            print(f"  {name}: {count}")
    else:
        print("  无")


def _print_gen_table(rows: dict) -> None:
    header = f"{'键':<22}{'总数':>6}{'成功':>6}{'失败':>6}{'成功率':>8}{'平均ms':>9}{'最大ms':>9}{'tokens':>10}"
    print(header)
    for key, value in rows.items():
        print(f"{key:<22}{value['total']:>6}{value['succeeded']:>6}{value['failed']:>6}{value['success_rate']:>8.2%}{value['avg_ms']:>9.1f}{value['max_ms']:>9.1f}{value['tokens']:>10}")


def main() -> int:
    parser = argparse.ArgumentParser(description="分析 Novel Ignite 运行日志")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="日志文件路径（默认 logs/app.jsonl）")
    parser.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = parser.parse_args()

    events = load_events(Path(args.log))
    if not events:
        print("没有可分析的事件。", file=sys.stderr)
        return 1
    report = summarize(events)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
