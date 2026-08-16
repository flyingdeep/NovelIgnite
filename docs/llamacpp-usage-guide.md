# llama.cpp + Qwen3.6-35B-A3B 推理服务访问指导文档

> 面向「把它当通用 LLM 服务接入」的用户：本服务提供 **OpenAI 兼容 API**，可用 openai SDK / requests / curl 直接调用，无需本地 GPU。
>
> **服务器**：`106.75.216.144`（Ubuntu 22.04.5，容器环境，PID1=tini + supervisord）
> **硬件**：AMD EPYC 7542 16 vCPU / 62GB RAM / NVIDIA RTX 4090 24GB（CUDA 13.2，驱动 595.80）
> **服务**：llama.cpp `llama-server`（CUDA 构建，v10298 / 15586e2d7），OpenAI 兼容 API
> **模型**：`Huihui-Qwen3.6-35B-A3B-abliterated`（Q4_K，21.7GB，MoE 激活约 3B，推理型）
> **文档最后更新**：2026-08-16（收尾验证完成）

---

## 1. 快速接入（30 秒上手）

| 项目 | 值 |
|---|---|
| Base URL | `http://106.75.216.144:57321/v1` |
| 模型名（`model` 字段） | `qwen3.6-35b-a3b` |
| 鉴权 | **无鉴权**（默认；可用 `--api-key` 开启，见 §10） |
| 公网状态 | **已验证可达**（2026-08-16，安全组已放行 TCP 57321） |
| 并发 | `--parallel 1` = **单并发**（同一时刻只能处理 1 个请求，多余请求排队） |

最快验证：

```bash
curl http://106.75.216.144:57321/v1/models
# → {"models":[{"id":"qwen3.6-35b-a3b",...}]}  HTTP 200
```

一个完整对话（关闭思考，快速响应）：

```bash
curl http://106.75.216.144:57321/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-35b-a3b",
    "messages": [{"role": "user", "content": "用一句话介绍你自己"}],
    "max_tokens": 128,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

---

## 2. 服务与模型信息

| 项目 | 值 |
|---|---|
| llama.cpp 源码 | `/workspace/llama.cpp`（git master，CUDA 后端） |
| llama-server 二进制 | `/workspace/llama.cpp/build/bin/llama-server` |
| 模型文件 | `/workspace/model/qwen3.6/Huihui-Qwen3.6-35B-A3B-abliterated-ggml-model-Q4_K.gguf` |
| 量化 | Q4_K（21.7GB = 21,712,409,824 字节） |
| 架构 | `qwen35moe`（总参 35.5B / 激活约 3B，带 MTP 头，默认忽略） |
| 监听 | `0.0.0.0:57321` |
| 上下文 | 16384（16K）；模型训练 ctx 262144 |
| 运行方式 | supervisord 托管，**随容器开机自启**（已确认机制） |
| 启动脚本 | `/workspace/llama-server-supervisord.sh` |
| 日志 | `/workspace/llama-server.log` |

**实测性能**（Q4_K，16K ctx，关闭思考）：

| 指标 | 实测值 |
|---|---|
| 生成速度 | **约 184-187 tok/s**（约 5.4 ms/token） |
| Prompt 处理 | 约 60-330 tok/s（短 prompt 更高） |
| 单请求总耗时示例 | 关闭思考 17 token 约 300ms；带思考 512 token 约 2.9s |

---

## 3. OpenAI 兼容接口

| 接口 | 路径 | 说明 |
|---|---|---|
| 模型列表 | `GET /v1/models` | 返回模型 `qwen3.6-35b-a3b` |
| 对话补全 | `POST /v1/chat/completions` | **推荐**，支持思考/工具/流式 |
| 文本补全 | `POST /v1/completions` | 纯文本补全（不走 chat 模板） |

> 请求/响应结构与 OpenAI 完全兼容；`model` 字段填任意非空字符串即可（服务端以 `--alias` 为准）。

---

## 4. 思考（推理）行为说明 —— 必读

本模型是**推理型模型**（Qwen3.6 系），回答前会先输出一段 `reasoning_content`（思考过程），再输出 `content`（最终答案）。

### 服务端默认配置（已固化）

- **默认开启思考**：启动参数含 `--chat-template-kwargs '{"enable_thinking":true}'`，不传参时模型会先思考。
- **思考深度不限**：服务端未设 `--reasoning-budget` 上限（默认 -1 即不限制），可进行较深推理。
- **不做强制限制**：未配置 `--reasoning off` 等禁用参数；客户端可随时自行控制。

### 客户端如何控制

| 目标 | 做法 |
|---|---|
| 关闭思考（快速直答） | 请求体加 `"chat_template_kwargs": {"enable_thinking": false}` |
| 开启思考（默认就是开） | 加 `"chat_template_kwargs": {"enable_thinking": true}` 或直接不传 |
| 控制思考深度 | 调大 `max_tokens`（思考 + 回答共用该额度；想深度思考至少 ≥512，推荐 1024+） |

### ⚠️ 空 content 的根因与排查（最常见问题）

思考型模型**先把 token 花在思考上**，再输出最终答案。若 `max_tokens` 太小，会出现：

```json
{"choices":[{"message":{"content":"","reasoning_content":"...（很长）..."},"finish_reason":"length"}]}
```

- **原因**：`max_tokens` 额度全部被 `reasoning_content` 消耗，`content` 还没开始就被截断。
- **解决**：
  - 需要思考：把 `max_tokens` 提到 **≥512**（深度思考建议 1024-2048）；
  - 不需要思考：加 `"chat_template_kwargs": {"enable_thinking": false}`，`max_tokens` 128 即可。

---

## 5. curl 示例

### 5.1 对话（默认思考，深度推理）

```bash
curl http://106.75.216.144:57321/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-35b-a3b",
    "messages": [{"role": "user", "content": "用一句话回答 7*8 等于多少"}],
    "max_tokens": 512
  }'
# 返回含 reasoning_content（思考）+ content（答案）
```

### 5.2 关闭思考（快速响应）

```bash
curl http://106.75.216.144:57321/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-35b-a3b",
    "messages": [{"role": "user", "content": "用一句话介绍杭州"}],
    "max_tokens": 256,
    "temperature": 0.7,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

### 5.3 流式输出（SSE）

```bash
curl -N http://106.75.216.144:57321/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-35b-a3b",
    "messages": [{"role":"user","content":"写一首关于秋天的诗"}],
    "max_tokens": 512,
    "stream": true,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
# 输出 data: {...} 分块，最后以 data: [DONE] 结束
```

### 5.4 文本补全

```bash
curl http://106.75.216.144:57321/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-35b-a3b","prompt":"The capital of France is","max_tokens":64}'
```

---

## 6. Python 示例

### 6.1 官方 openai SDK（推荐）

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://106.75.216.144:57321/v1",
    api_key="sk-any-nonempty",  # 服务未开 --api-key 时填任意字符串即可
)

# ① 默认：开启思考，深度推理（max_tokens 足够大，避免 content 被截断为空）
resp = client.chat.completions.create(
    model="qwen3.6-35b-a3b",
    messages=[{"role": "user", "content": "用一句话回答 7*8 等于多少"}],
    max_tokens=512,
)
print("思考:", resp.choices[0].message.reasoning_content)  # 可能为 None
print("答案:", resp.choices[0].message.content)

# ② 关闭思考：快速直答
resp = client.chat.completions.create(
    model="qwen3.6-35b-a3b",
    messages=[{"role": "user", "content": "1+1=?"}],
    max_tokens=128,
    temperature=0.3,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
print(resp.choices[0].message.content)

# ③ 流式（SSE）：思考型建议关闭思考或加大 max_tokens
stream = client.chat.completions.create(
    model="qwen3.6-35b-a3b",
    messages=[{"role": "user", "content": "写一首关于秋天的诗"}],
    max_tokens=512,
    stream=True,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 6.2 纯 requests（无第三方依赖）

```python
import requests

# 开启思考
r = requests.post(
    "http://106.75.216.144:57321/v1/chat/completions",
    json={
        "model": "qwen3.6-35b-a3b",
        "messages": [{"role": "user", "content": "1+1=?"}],
        "max_tokens": 512,
    },
    timeout=120,
)
msg = r.json()["choices"][0]["message"]
print("思考:", msg.get("reasoning_content"))
print("答案:", msg.get("content"))

# 关闭思考
r = requests.post(
    "http://106.75.216.144:57321/v1/chat/completions",
    json={
        "model": "qwen3.6-35b-a3b",
        "messages": [{"role": "user", "content": "1+1=?"}],
        "max_tokens": 128,
        "chat_template_kwargs": {"enable_thinking": False},
    },
    timeout=120,
)
print(r.json()["choices"][0]["message"]["content"])
```

---

## 7. 参数建议

| 参数 | 建议 | 说明 |
|---|---|---|
| `max_tokens` | 关思考 128-256；开思考 **≥512**，深度思考 1024-2048 | 思考 + 回答共用额度；太小会截断（content 为空） |
| `temperature` | 事实问答 0.1-0.3；创意/对话 0.7-0.9 | 与 OpenAI 语义一致 |
| `top_p` | 默认即可，或 0.8-0.9 | 与 temperature 二选一微调 |
| `stream` | 聊天场景建议 `true` | SSE 流式，降低首 token 等待感 |
| `enable_thinking` | 默认 true；要快就 false | 见 §4 |
| 并发 | 单请求 | `--parallel 1`，多个并发请求会排队 |

---

## 8. 服务端配置摘要（只读参考）

启动脚本 `/workspace/llama-server-supervisord.sh` 固化参数：

| 参数 | 值 | 说明 |
|---|---|---|
| `--host/--port` | 0.0.0.0 / 57321 | 公网监听 |
| `--alias` | qwen3.6-35b-a3b | 模型别名 |
| `--ctx-size` | 16384 | 16K 上下文 |
| `--n-gpu-layers` | 99 | 全层上 GPU（显存 21155/24564 MiB = 86%） |
| `--threads / --threads-batch` | 16 / 8 | CPU 线程（MoE expert 部分走 CPU） |
| `--parallel` | 1 | 单并发 |
| `--cache-type-k/v` | q8_0 | KV 量化省显存 |
| `--flash-attn` | on | Flash Attention |
| `--jinja` | on | 模型自带 chat 模板 |
| `--chat-template-kwargs` | `{"enable_thinking":true}` | **服务端默认开启思考** |

**MTP（多头预测）说明**：当前 llama.cpp 构建支持 `--spec-type draft-mtp`，且本模型带 MTP 头。实测开启后显存 +828MiB（86%→89.5%），但生成速度由 ~186 降至 ~165 tok/s（该模型激活仅 3B，速度已接近显存带宽上限，MTP 纯增验证开销反而更慢），因此**已回滚，保持默认忽略 MTP 层**。日志中 `unused tensor blk.40.nextn.*` 提示属正常。

---

## 9. 服务管理（运维）

SSH：`ssh -p 23 root@106.75.216.144`

```bash
supervisorctl status llamaserver        # 状态
supervisorctl restart llamaserver       # 重启（模型重载约 3-5 分钟）
supervisorctl stop llamaserver
tail -f /workspace/llama-server.log     # 日志
```

**开机自启机制（已确认）**：容器启动 → `tini`（PID1）→ `supervisord`（nodaemon 前台）→ `llamaserver`（`autostart=true` + `autorestart=true`），**容器重启后 llama-server 会自动拉起**，无需手动干预。

---

## 10. 常见问题（FAQ）

### Q1: 返回 content 为空，只有 reasoning_content？
- 思考型模型正常现象：token 全花在思考上，`max_tokens` 不够。
- 解决：`max_tokens` 提到 ≥512（深度思考 1024+），或加 `chat_template_kwargs.enable_thinking=false`。

### Q2: 公网连不上？
- 服务监听 `0.0.0.0:57321`，安全组已放行（2026-08-16 验证可达）。
- 若仍不通：`curl -v` 看是否超时 → 检查云安全组入方向 TCP 57321 是否被改回；本地 `Test-NetConnection 106.75.216.144 -Port 57321`。

### Q3: 请求超时/很慢？
- 首次请求或重启后需等模型加载（3-5 分钟），期间会拒绝/超时。
- 带思考 + 大 max_tokens 单次最多约 3-5 秒；若排队（单并发）会叠加等待。

### Q4: 显存不足（CUDA OOM）？
- 当前 21155/24564 MiB（86%），余量约 3.4GB。
- 若 OOM：降低 `--ctx-size`（如 8192）、KV 用 `q4_0`、或 `--n-gpu-layers` 降到 60 让部分层走 CPU（62GB 内存充足）。

### Q5: 并发说明？
- `--parallel 1` = **单并发**：同一时刻只处理 1 个请求，其余排队。高并发接入建议后期评估 `--parallel`（需先确认显存/内存余量）。

### Q6: 如何加鉴权？
- 启动脚本加 `--api-key <密钥>` 后 `supervisorctl restart llamaserver`。
- 客户端加 `Authorization: Bearer <密钥>`；openai SDK 填 `api_key`。

### Q7: 重启后没自动启动？
- 正常不会：supervisord `autostart=true` + 容器自启链已确认。
- 若容器重建导致 supervisord 配置丢失，重新执行安装脚本并 `supervisorctl start llamaserver`。

### Q8: 磁盘空间？
- 当前 79GB 已用 65GB，剩约 11GB。如需释放：`ollama rm huihui_aiQwen3.6-abliterated-27b:latest` 可释放 17GB（影响 ollama 服务，先确认）。

---

## 11. 实测验证记录（2026-08-16 收尾）

- `GET /v1/models`：HTTP 200，约 21ms。
- 公网 chat（关闭思考）：「用一句话介绍你自己」→ 17 token，总耗时约 302ms，`finish=stop`。
- 公网 chat（默认思考）：「7*8 等于多少」→ 512 token 全为思考，总耗时约 2.93s（验证默认思考开启、公网可达）。
- 生成速度（关闭思考，3 次）：184.2 / 186.3 / 187.3 tok/s。
- 思考开关三态验证：默认=开（reasoning 383 字符）/ `enable_thinking=false`→content='1+1=2' / `enable_thinking=true`→reasoning 779 字符。
- MTP 实测：`--spec-type draft-mtp` 加载成功（+828MiB 显存），速度降至 ~165 tok/s，**已回滚**。
- 日志错误数：0。

---

## 12. 安全提醒

- 当前服务**无鉴权**且公网可达，**强烈建议配置 `--api-key`**，并在安全组限制来源 IP。
- 开放端口 57321 已放行全公网（用户决策），请注意被扫描滥用风险。
- 服务器 root 密码曾明文出现于对话，**建议尽快轮换**并改用 SSH 密钥登录。

---

*文档更新：2026-08-16*
