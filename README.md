# Novel Ignite

Novel Ignite 是“作者确认优先”的 AI 小说创作 MVP。当前真实后端与原型工作台支持：

```text
作品库 → Idea → Story Concept → Story Blueprint → Chapter Plan → Chapter Workspace → Novel Reader
```

AI 输出始终是候选内容，只有作者显式确认或应用后才会成为权威数据。

## 当前可操作范围

1. 作品库：创建、读取、软删除作品。
2. Idea：保存原始创意；Concept 生成后自动锁定，只读浏览。
3. Story Concept：真实 OpenAI Chat Completions 兼容模型生成候选，支持编辑、Lock、确认与版本控制。
4. Story Blueprint：生成 Characters、World、Initial Timeline、Story Arc 四类 Baseline，支持编辑、Lock、确认与版本履历。
5. Living State：Blueprint 确认后自动创建初始投影；每确认一章 Chapter Delta 生成一个新版本（v1→v2→…），并投影三域状态与章节事件推进；支持按版本查看更新履历。
6. Chapter Plan：根据已确认 Blueprint 生成章节卡片；第 1 章为 `fixed + active`，后续章节为 `outline + locked`。
7. **步骤条阶段约束**：顶部 1–6 步按 Story 阶段锁定——概念/蓝图/章节/工作台/阅读仅在对应阶段推进后才解锁（未解锁步骤灰显，点击被阻止并提示原因）；进入故事时从后端刷新真实阶段。蓝图未确认前无法进入章节/工作台/阅读，避免看到残留占位。
8. Chapter Workspace：Chapter Context（Snapshot + Events + Scenes + Beats）、场景/节拍规划、正文生成与应用（append-only 版本，自动接受）、工作台内 Markdown 编辑（作者可直接修改正文后应用，创建新版本、保留历史）、Chapter Delta 合并与作者确认、下一章激活、后续章节过期标记。
9. AI 驱动的 Delta 提取与一致性检查：生成/应用正文后由模型基于本章入口快照提取角色/世界/时间线变化（失败回退到确定性规则），并输出一致性发现（与快照矛盾、时间线冲突、已确认事实违背），全部作为 proposed 候选或提醒展示，不自动覆盖作者确认的事实；确定性规则（过短/占位标记）始终叠加运行。
10. Scene Summary：场景全部 Beat 完成后自动生成场景摘要（模型失败回退到正文片段），工作台与阅读模式均展示；后续场景的生成提示会注入前序已完结场景的摘要以保持剧情连贯（“修订后续计划”）。
11. 一致性检查：生成正文后自动跑确定性一致性规则（过短/占位标记），问题以提醒展示，不阻止写作。
12. 阅读模式（全书完结）：确认最后一章 Chapter Delta 后进入结算画面（第 6 步）阅读完整小说；左侧章节列表、右侧连贯正文，Scene 作为「节」导航锚点；已完成作品从作品库直接进入阅读模式。

## 启动

需要 Python 3.12+（已使用 Python 3.13 验证）。在仓库根目录执行：

```powershell
py -3.13 -m pip install -e ".[dev]"
Copy-Item .env.example .env
py -3.13 -m alembic upgrade head
py -3.13 -m uvicorn app.main:app --reload
```

> **从旧版本升级：** 如果你此前使用过旧 v1 结构库（`stories` 表缺少 `stage`/`idea_text` 列），直接启动会在 `/api/v1/works` 返回 500。此时请先备份并重建数据库：
>
> ```powershell
> Copy-Item novel_ignite.db novel_ignite_v1_archived.db   # 备份旧数据
> Remove-Item novel_ignite.db
> py -3.13 -m alembic upgrade head                        # 从零创建新结构库
> ```
>
> 旧库备份 `novel_ignite_v1_archived.db` 已被 `.gitignore` 排除，不会提交。

访问：

- `http://127.0.0.1:8000/`：当前原型与真实 Phase 1–6 API（前端挂载于根路径，文件位于 `prototype/`）。
- `http://127.0.0.1:8000/docs`：Swagger API 文档。
- `http://127.0.0.1:8000/health`：健康检查。

## 模型接入

四种模型均使用 OpenAI Python SDK + Chat Completions：

| 提供方 | Base URL | 默认模型 | 环境变量 | JSON 说明 |
|---|---|---|---|---|
| Agnes | `https://apihub.agnes-ai.com/v1` | `agnes-2.5-flash` | `AGNES_API_KEY` | 支持 `response_format`；思考模式经 `chat_template_kwargs.enable_thinking` 开启 |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-v4-flash` | `DEEPSEEK_API_KEY` | 可尝试 JSON 模式；思考模式默认开启，`extra_body.thinking` + 顶层 `reasoning_effort` |
| Grok | `https://modelflare.dev/v1` | `grok-4.5` | `GROK_API_KEY` | 不发送 `response_format`，自动容错解析；推理内置，顶层 `reasoning_effort` |
| llama.cpp（远端） | `http://106.75.216.144:57321/v1` | `qwen3.6-35b-a3b` | `LLAMACPP_API_KEY`（可选，通常无鉴权） | 支持 `response_format`；Qwen3.6 推理经 `chat_template_kwargs.enable_thinking` 开关（low 关闭）；**始终以流式请求**（绕开公网链路对非流式长请求的 ~60s 空闲断连） |

- 推理强度（low/medium/high）按各模型官方文档传递：DeepSeek 顶层 `reasoning_effort`（medium 映射 high）、Agnes `chat_template_kwargs.enable_thinking`、Grok 顶层 `reasoning_effort`、llama.cpp（Qwen3.6）`chat_template_kwargs.enable_thinking`（low 视为关闭思考）。
- 各模型最大输出按官方上限：Agnes 2.5 65.5K / DeepSeek v4-flash 384K / Grok 4.5 500K / llama.cpp 8K（服务器 ctx 16K，为输入留余量）；生成调用默认使用该上限。
- **模型可用性异步探测**：`GET /api/v1/models/availability` 返回每个模型的可用状态——llama.cpp 做真实网络探测（`GET {base}/models`，服务器离线则 `available=false`），其余按 API Key 是否配置判断；前端页面加载时异步调用，**不可用模型在生成设置下拉中置为禁用**（llama.cpp 离线时显示「离线 · 不可用」）。
- llama.cpp 单次请求超时 300s（远端单并发 + 思考占用时间较长），其余模型沿用全局超时；llama.cpp 无鉴权，始终构建适配器（是否可用由探测决定）。

- `.env` 只在服务端读取，不能提交到 Git。
- 模型、Temperature 和推理强度可以通过作品级 AI 配置保存。
- **系统提示词集中管理**：所有生成任务的 system prompt 统一维护在 `app/infrastructure/prompts.py`（按 action 索引，含 `SYSTEM_PROMPTS` 与 `PROMPT_VERSIONS`）；修改一处全局生效，`system_prompt(action)` / `prompt_version(action)` 供服务层引用。
- 每次生成任务记录模型参数快照与**所用提示词版本**（`generation_tasks.prompt_version`），不记录密钥、完整提示词或正文全文。
- 无模型 Key 时使用可复现的 fallback / fake 流程进行离线开发和测试。

## 手工验收路径

1. 在作品库创建作品，输入 Idea 并保存。
2. 点击「AI生成概念」，审核 Concept 候选，编辑或锁定字段后确认；确认后**自动生成 Blueprint 候选**并进入蓝图页。
3. 在 Blueprint 查看 Characters / World / Timeline / Arc（已自动生成，无需再点生成候选）；若确认概念后自动生成中断/失败（如刷新页面），进入蓝图页会自动**补齐生成**（自愈），失败则显示空状态并提示点击「生成候选」重试。
4. 确认四类 Blueprint，观察 Story 进入 `blueprint_confirmed` 并生成初始 Living State。
5. 进入 Chapter Plan，点击「生成章节雏形」。
6. 确认第 1 章为 active，其余章节为 locked；锁定章节不能进入或修改。
7. 进入 Chapter Workspace：生成场景计划 → 逐场景生成节拍计划 → 生成正文（自动应用，可再次生成新版本）→ 全部 Beat 应用后确认 Chapter Delta，Living State 升为新版本并激活下一章。
8. 在蓝图的「Living State」页查看各版本更新履历；在已完成章节的工作台可只读查看历史。
9. 全书完结：确认最后一章 Delta 后自动进入阅读模式，左侧章节列表 + 右侧连贯正文 + Scene「节」导航；已完成作品从作品库点击封面直接进入阅读。

所有写操作使用 `expected_version` 做乐观锁；状态、版本或 Lock 冲突会返回 `409`。

## 可观测性

- `GET /metrics`：JSON 指标快照（请求数/状态码分布、生成任务成功率/平均与最大耗时、按 action 与模型统计、错误类型计数、`error_categories` 失败类别计数、最近事件）。
- 每次生成写入 `generation_tasks.prompt_version`（所用提示词版本号），与 `model_snapshot` 一起支持按版本追溯生成结果；提示词内容变更时在 `app/infrastructure/prompts.py` 递增对应版本号。
- **LLM 调用失败可溯源**：每次失败记录 `error_type`（异常类）、`error_code`（提供商错误码，如 `content_filter`）、`http_status`（如 400/429/502）、`error_category`（`timeout`/`connection`/`auth`/`rate_limit`/`content_policy`/`bad_request`/`server`/`api`…）以及脱敏截断的 `error_detail`（API 返回的错误说明），可直接区分超时、合规性拒绝、限流、参数错误等真实原因；当模型返回**合规拒绝文本**（而非 JSON，如「无法生成/抱歉/内容政策」）时，`extract_json` 会将其归类为 `ContentPolicyRefusalError`（`error_category=content_policy`），不再与「输出格式错误」混淆；`/metrics` 的 `errors` 与 `error_categories` 按计数聚合。
- `logs/app.jsonl`：结构化 JSONL 日志（请求、生成调用：模型/耗时/token/状态/错误类型/错误码/HTTP 状态/失败类别/脱敏错误说明、请求异常）。隐私约束：不记录完整提示词、正文与 API Key；错误说明仅取 API 返回的失败信息并截断；日志目录被 `.gitignore` 排除。
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
- `GET /api/v1/stories/{id}/living-state/history`
- `GET /api/v1/stories/{id}/chapters`
- `POST /api/v1/stories/{id}/chapter-plan`
- `GET /api/v1/stories/{id}/chapters/{chapter_id}`
- `PUT /api/v1/stories/{id}/chapters/{chapter_id}/plan`
- `GET /api/v1/stories/{id}/chapters/{chapter_id}/context`
- `GET /api/v1/stories/{id}/read`（全书阅读模式：所有章节 + 场景 + 已应用正文）
- `POST /api/v1/stories/{id}/chapters/{chapter_id}/generations`（scene-plan / beat-plan / generate_scene / generate_chapter_remaining / regenerate_beat）
- `POST /api/v1/stories/{id}/chapters/{chapter_id}/scenes/{scene_id}/generations`（scene-plan / beat-plan / generate_scene / generate_beat / regenerate_beat）
- `POST /api/v1/stories/{id}/chapters/{chapter_id}/backfill`（补全历史章节缺失正文，使用章节入口快照）
- `POST /api/v1/stories/{id}/chapters/{chapter_id}/scenes/{scene_id}/beats/{beat_id}/prose-versions`
- `GET /api/v1/stories/{id}/chapters/{chapter_id}/scenes/{scene_id}/beats/{beat_id}/prose`
- `GET /api/v1/stories/{id}/chapters/{chapter_id}/deltas`
- `POST /api/v1/stories/{id}/chapters/{chapter_id}/deltas/confirm`
- `GET /api/v1/stories/{id}/chapters/{chapter_id}/issues`

## 测试与迁移

```powershell
py -3.13 -m alembic upgrade head
py -3.13 -m pytest -q
```

当前回归结果：**61 passed（单元/集成）＋ 13 passed（E2E）**。覆盖作品库、Idea 锁定、AI 配置、四模型适配（含思考/推理参数、官方 max token 与 Ollama 流式）、Concept 候选/确认与卖点规范化、Blueprint 四分类全条目渲染、Living State 初始投影、Chapter Plan 逐章激活与锁定章节保护、标题生成、可观测性指标（Phase 1–4）；Chapter Workspace 快照/上下文、Scene / Beat 规划与乐观锁、正文自动应用与版本追溯、Chapter Delta 确认（含完整性校验）、缺失正文补全、Living State 版本递增、一致性检查、全书阅读模式数据（Phase 5–6）；以及 AI 驱动 Delta 提取、AI 一致性发现、Scene Summary 生成与前置摘要注入、逐个 Beat 生成自动完结场景（Phase 6 增强）、内容策略拒绝文本识别（`ContentPolicyRefusalError`）、蓝图缺失自愈与演示数据清理、模型可用性异步探测与离线禁用；Playwright 端到端（E2E）覆盖作品库→创意→概念→蓝图→章节→工作台正文编辑/生成→阅读模式全流程。

E2E 运行方式（建议使用无 API Key 的独立服务器走确定性回退，快速稳定）：

```powershell
# 终端 1：E2E 专用服务器（独立数据库 + 无 Key）
$env:DATABASE_URL="sqlite:///./e2e_test.db"
$env:AGNES_API_KEY=""; $env:DEEPSEEK_API_KEY=""; $env:GROK_API_KEY=""
py -3.13 -m alembic upgrade head
py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8010

# 终端 2：运行 E2E
$env:NOVEL_SERVER_URL="http://127.0.0.1:8010"
py -3.13 -m pytest tests/e2e -v
```

## 目录

- `app/api/`：FastAPI 路由与 DTO。
- `app/works/`：作品库、Concept、Blueprint、Living State 服务与模型。
- `app/planning/`：Chapter Plan、Chapter Workspace（Snapshot/Events/Scenes/Beats）、写作服务（Prose/Delta/Consistency）。
- `app/infrastructure/`：配置、SQLite、SQLAlchemy、模型适配器、**提示词集中管理（`prompts.py`）**、可观测性（指标/日志）。
- `app/lore/`：全局实体领域预留。
- `app/writing/`：正文生成领域预留。
- `app/consistency/`：Snapshot、Delta、一致性领域预留。
- `prototype/`：UI 交互事实来源与当前原型前端。
- `migrations/`：Alembic 迁移。
- `tests/`：Phase 1–6 单元/集成测试与 E2E 冒烟测试。
