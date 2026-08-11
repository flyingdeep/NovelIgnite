"""真实模型连通性验证：逐个调用已配置的 Agnes / DeepSeek / Grok 生成 Story Concept。

运行：py -3.13 scripts/verify_models.py
注意：会真实消耗模型额度；不打印任何 API Key。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.config import get_settings
from app.projects.service import build_model_adapters

IDEA = "一位记忆鉴定师发现自己的过去正在地下拍卖场被分批出售，他决定潜入拍卖场找回属于自己的记忆。"


def main() -> int:
    settings = get_settings()
    adapters = build_model_adapters(settings)
    failed = False
    for provider in ("agnes", "deepseek", "grok"):
        adapter = adapters.get(provider)
        if adapter is None:
            print(f"[{provider}] SKIP 未配置 API Key")
            continue
        model_name = getattr(getattr(adapter, "spec", None), "model_name", "?")
        print(f"[{provider}] 调用 {model_name} ...", flush=True)
        try:
            result = adapter.generate_concept(IDEA, {})
            keys = sorted(result.keys())
            sample = result.get("genre") or result.get("synopsis") or ""
            print(f"[{provider}] OK 键={keys} 示例={str(sample)[:60]!r}")
        except Exception as exc:  # noqa: BLE001
            failed = True
            print(f"[{provider}] FAIL {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
