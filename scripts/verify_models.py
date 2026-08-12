"""真实模型连通性验证：逐个调用已配置的 Agnes / DeepSeek / Grok 生成 Story Concept。

运行：py -3.13 scripts/verify_models.py
注意：会真实消耗模型额度；不打印任何 API Key。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.config import settings
from app.infrastructure.model_adapter import build_adapters, configured_model_specs

IDEA = "一只被遗弃的橘猫和一只走失的狗在寒夜街头相遇，共同抵御灾难，建立起超越物种的羁绊。"


def main() -> int:
    adapters = build_adapters()
    specs = {spec.provider: spec for spec in configured_model_specs()}
    failed = False
    for provider, spec in specs.items():
        adapter = adapters.get(provider)
        if adapter is None:
            print(f"[{provider}] SKIP 未配置 API Key")
            continue
        print(f"[{provider}] 调用 {spec.model} ...", flush=True)
        try:
            text = adapter.complete(
                [{"role": "user", "content": f"请根据创意生成一个极简 Story Concept（JSON）：{IDEA}"}],
                temperature=0.7,
                reasoning_strength="medium",
                json_mode=spec.supports_json,
                max_tokens=4096,
            )
            print(f"[{provider}] OK 输出长度={len(text or '')} 示例={str(text)[:60]!r}")
        except Exception as exc:  # noqa: BLE001
            failed = True
            print(f"[{provider}] FAIL {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
