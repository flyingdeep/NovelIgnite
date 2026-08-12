# 三种 LLM 临时接入参考

> 基于当前 `openvideofactory_app` 的实际配置，供其他项目快速复用。三种模型均使用 **OpenAI Python SDK + Chat Completions**，只需替换 `base_url`、`model` 和 API Key 环境变量。

## 模型配置

| 模型 | `base_url` | `model` | API Key 环境变量 | 备注 |
|---|---|---|---|---|
| Agnes | `https://apihub.agnes-ai.com/v1` | `agnes-2.5-flash` | `AGNES_API_KEY` | OpenAI 兼容；思考模式经 `chat_template_kwargs.enable_thinking` 开启；`agnes-2.0-flash` 仍可作为兼容回退 |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-v4-flash` | `DEEPSEEK_API_KEY` | OpenAI 兼容；思考模式默认开启，需 `extra_body.thinking={type:enabled}` + 顶层 `reasoning_effort`；思考模式下 `temperature` 不生效 |
| Grok | `https://modelflare.dev/v1` | `grok-4.5` | `GROK_API_KEY` | OpenAI 兼容；推理无法关闭（默认 high），顶层 `reasoning_effort`(low/medium/high)；不发送 `response_format` |

## 思考 / 推理模式

| 模型 | 开启方式 | 强度参数 |
|---|---|---|
| DeepSeek | `extra_body: {"thinking": {"type": "enabled"}}`（文档说明默认已开启，仍显式开启） | 顶层 `reasoning_effort`: low/high/max；映射 low→low、medium→high、high→high |
| Agnes 2.5 | `extra_body: {"chat_template_kwargs": {"enable_thinking": true}}` | 无强度档位（`low` 可传 false 关闭）；Anthropic 兼容格式支持 `budget_tokens` |
| Grok | 推理内置，无法关闭 | 顶层 `reasoning_effort`: low/medium/high，默认 high |

说明：

- DeepSeek 思考模式下 `temperature`/`top_p`/`presence_penalty`/`frequency_penalty` 不生效（设置不报错）。
- 思维链通过响应 `reasoning_content` 返回；本项目为一次性生成任务，不参与多轮拼接。
- `reasoning_effort` 对 DeepSeek/Grok 是**顶层参数**，不要放进 `extra_body`；Agnes 不用 `reasoning_effort`。

## 最小调用形式

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="替换为上表地址",
    api_key=os.environ["对应的_API_KEY_环境变量"],
    timeout=180,
)

response = client.chat.completions.create(
    model="替换为上表 model",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "你好，请简短回复。"},
    ],
    temperature=0.2,
    max_tokens=4096,
)

text = response.choices[0].message.content or ""
```

## JSON 输出

Agnes 和 DeepSeek 通常可尝试：

```python
response_format={"type": "json_object"}
```

Grok 在当前项目中标记为不支持该参数，因此不要发送 `response_format`；应在提示词中要求“只返回合法 JSON”，然后由调用方解析和校验。

## 环境变量

在项目 `.env` 中配置（不要把真实 Key 提交到 Git）：

```text
AGNES_API_KEY=...
DEEPSEEK_API_KEY=...
GROK_API_KEY=...
```

## 注意

- `base_url` 是 SDK 的 API 根地址，不要再额外拼接 `/chat/completions`；SDK 会调用 `POST {base_url}/chat/completions`。
- 当前项目的模型 ID 是项目预设中的实际字符串；如果服务商账号下的模型名称不同，应以服务商控制台为准。
- API Key 只从环境变量读取，不写入项目 JSON、数据库或前端。
- 这是临时参考文档；端点、模型名和参数支持情况可能随服务商调整。
