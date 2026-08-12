# Novel Ignite

Novel Ignite 是“作者确认优先”的 AI 小说创作 MVP。当前真实后端与原型工作台支持：

```text
作品库 → Idea → Story Concept → Story Blueprint → Chapter Plan
```

AI 输出始终是候选内容，只有作者显式确认或应用后才会成为权威数据。

## 当前可操作范围

1. 作品库：创建、读取、软删除作品。
2. Idea：保存原始创意；Concept 生成后自动锁定，只读浏览。
3. Story Concept：真实 OpenAI Chat Completions 兼容模型生成候选，支持编辑、Lock、确认与版本控制。
4. Story Blueprint：生成 Characters、World、Initial Timeline、Story Arc 四类 Baseline，支持编辑、Lock、确认与版本履历。
5. Living State：四类 Blueprint Baseline 确认后自动创建初始投影。
6. Chapter Plan：根据已确认 Blueprint 生成章节卡片；第 1 章为 `fixed + active`，后续章节为 `outline + locked`。

Chapter Workspace、Chapter Context、Scene / Beat 规划、正文生成、State Delta 和 Next Chapter 属于后续 Phase。

## 启动

需要 Python 3.12+（已使用 Python 3.13 验证）。在仓库根目录执行：

```powershell
py -3.13 -m pip install -e ".[dev]"
Copy-Item .env.example .env
py -3.13 -m alembic upgrade head
py -3.13 -m uvicorn app.main:app --reload
```

> **从旧版本升级：** 如果你此前使用过旧实现（`app_v1_archived`），本地 `novel_ignite.db` 可能是旧结构库（`stories` 表缺少 `stage`/`idea_text` 列），直接启动会在 `/api/v1/works` 返回 500。此时请先备份并重建数据库：
>
> ```powershell
> Copy-Item novel_ignite.db novel_ignite_v1_archived.db   # 备份旧数据
> Remove-Item novel_ignite.db
> py -3.13 -m alembic upgrade head                        # 从零创建新结构库
> ```
>
> 旧库已归档为 `novel_ignite_v1_archived.db`（已被 `.gitignore` 排除，不会提交）。

访问：

- `http://127.0.0.1:8000/prototype/`：当前原型与真实 Phase 1–4 API。
- `http://127.0.0.1:8000/docs`：Swagger API 文档。
- `http://127.0.0.1:8000/health`：健康检查。

## 模型接入

三种模型均使用 OpenAI Python SDK + Chat Completions：

| 提供方 | Base URL | 默认模型 | 环境变量 | JSON 说明 |
|---|---|---|---|---|
| Agnes | `https://apihub.agnes-ai.com/v1` | `agnes-2.5-flash` | `AGNES_API_KEY` | 支持 `response_format`；思考模式经 `chat_template_kwargs.enable_thinking` 开启 |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-v4-flash` | `DEEPSEEK_API_KEY` | 可尝试 JSON 模式；思考模式默认开启，`extra_body.thinking` + 顶层 `reasoning_effort` |
| Grok | `https://modelflare.dev/v1` | `grok-4.5` | `GROK_API_KEY` | 不发送 `response_format`，自动容错解析；推理内置，顶层 `reasoning_effort` |

- 推理强度（low/medium/high）按各模型官方文档传递：DeepSeek 顶层 `reasoning_effort`（medium 映射 high）、Agnes `chat_template_kwargs.enable_thinking`、Grok 顶层 `reasoning_effort`。
- 各模型最大输出按官方上限：Agnes 2.5 65.5K / DeepSeek v4-flash 384K / Grok 4.5 500K；生成调用默认使用该上限。

- `.env` 只在服务端读取，不能提交到 Git。
- 模型、Temperature 和推理强度可以通过作品级 AI 配置保存。
- 每次生成任务记录模型参数快照，不记录密钥、完整提示词或正文全文。
- 无模型 Key 时使用可复现的 fallback / fake 流程进行离线开发和测试。

## 手工验收路径

1. 在作品库创建作品，输入 Idea 并保存。
2. 点击「AI生成概念」，审核 Concept 候选，编辑或锁定字段后确认；确认后**自动生成 Blueprint 候选**并进入蓝图页。
3. 在 Blueprint 查看 Characters / World / Timeline / Arc（已自动生成，无需再点生成候选）。
4. 确认四类 Blueprint，观察 Story 进入 `blueprint_confirmed` 并生成初始 Living State。
5. 进入 Chapter Plan，点击「生成章节雏形」。
6. 确认第 1 章为 active，其余章节为 locked；锁定章节不能进入或修改。

所有写操作使用 `expected_version` 做乐观锁；状态、版本或 Lock 冲突会返回 `409`。

## 可观测性

- `GET /metrics`：JSON 指标快照（请求数/状态码分布、生成任务成功率/平均与最大耗时、按 action 与模型统计、错误类型计数、最近事件）。
- `logs/app.jsonl`：结构化 JSONL 日志（请求、生成调用：模型/耗时/token/状态/错误类型、请求异常）。隐私约束：不记录完整提示词、正文与 API Key；日志目录被 `.gitignore` 排除。
- 日志轮转：单文件超过 5MB 自动滚动为 `app.jsonl.1/.2/…`，保留最近 5 份；可用环境变量 `NOVEL_LOG_DIR`、`NOVEL_MAX_LOG_BYTES` 覆盖。
- 分析脚本：`py -3.13 scripts/analyze_metrics.py`（终端报表：按 action/模型的成功率、平均/最大耗时、token、错误类型、最慢请求/生成）；`--json` 输出结构化数据便于程序化分析。

## 主要 API

- `GET /health`、`GET /metrics`
- `GET/POST/DELETE /api/v1/works`
- `PUT /api/v1/stories/{id}/idea`
- `GET/PUT /api/v1/stories/{id}/ai-config`
- `GET /api/v1/models`
- `GET /api/v1/stories/{id}/concept`
- `POST /api/v1/stories/{id}/generations`
- `PUT /api/v1/stories/{id}/concept`
- `POST /api/v1/stories/{id}/concept/confirm`
- `GET /api/v1/stories/{id}/blueprint`
- `POST /api/v1/stories/{id}/blueprint/generations`
- `PUT /api/v1/stories/{id}/blueprint/{kind}`
- `POST /api/v1/stories/{id}/blueprint/confirm`
- `GET /api/v1/stories/{id}/chapters`
- `POST /api/v1/stories/{id}/chapter-plan`
- `GET /api/v1/stories/{id}/chapters/{chapter_id}`
- `PUT /api/v1/stories/{id}/chapters/{chapter_id}/plan`

## 测试与迁移

```powershell
py -3.13 -m alembic upgrade head
py -3.13 -m pytest -q
```

当前回归结果：**22 passed**。覆盖作品库、Idea 锁定、AI 配置、三模型适配（含思考/推理参数与官方 max token）、Concept 候选/确认与卖点规范化、Blueprint 四分类全条目渲染、Living State 初始投影、Chapter Plan 逐章激活与锁定章节保护、标题生成、可观测性指标。

## 目录

- `app/api/`：FastAPI 路由与 DTO。
- `app/works/`：作品库、Concept、Blueprint 服务与模型。
- `app/planning/`：Chapter Plan 模型、生成和访问控制。
- `app/infrastructure/`：配置、SQLite（WAL 并发）、SQLAlchemy、模型适配器、可观测性（指标/日志）。
- `app/lore/`：全局实体领域预留。
- `app/writing/`：正文生成领域预留。
- `app/consistency/`：Snapshot、Delta、一致性领域预留。
- `prototype/`：UI 交互事实来源与当前原型前端。
- `migrations/`：Alembic 迁移。
- `tests/`：新工程 Phase 1–4 测试。
- `app_v1_archived/`、`tests_v1_archived/`、`migrations/versions_v1_archived/`：旧实现归档。
