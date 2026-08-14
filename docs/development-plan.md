# Novel Ignite 开发计划 v2

> 产品需求事实来源：`../NOVEL_IGNITE_需求文档_V2.md`  
> 技术实现事实来源：`technical-architecture.html`  
> UI 交互事实来源：`../prototype/index.html`（唯一权威参考）

## MVP 原则

按功能递进分 Phase 交付，每个 Phase 必须产出**可独立验证的纵向切片**（数据 → 服务 → API → 前端 → 测试），不允许只堆积后台模型或静态页面。每一 Phase 完成后作者应能在浏览器中完成该阶段对应的真实操作。

## MVP 完成定义

作者从作品库创建故事、输入创意、生成并确认 Concept 与 Blueprint、进入 Chapter Plan、在唯一的 Chapter Workspace 中按 Scene → Beat → Prose → Delta 顺序完成当前章写作，确认后 Story State 更新并进入下一章。

---

## Phase 1｜基础框架 + 后端 + 大模型 + 前端 UI 框架 + 作品库

**目标：** 建立可运行的全栈骨架，交付作品库纵向切片，验证原型到后端的完整链路。

### 1.1 工程骨架
- [x] FastAPI 应用、CORS、静态文件挂载（`prototype/` 通过 `/prototype` 访问）。
- [x] SQLAlchemy 2.x + SQLite 数据库引擎与 session 工厂。
- [x] Alembic 初始迁移（`stories` 表含 stage/idea_text/version/deleted_at）。
- [x] Pydantic-settings 配置（`.env` 读取 `DATABASE_URL` 与模型密钥）。
- [x] pytest 基础 fixture（测试空库、fake adapter）。

### 1.2 大模型适配层
- [x] OpenAI Chat Completions 兼容适配器接口（`ModelAdapter` 协议）。
- [x] 三模型实现：Agnes / DeepSeek / Grok（按 `response_format` 支持差异化处理）。
- [x] 容错 JSON 提取（markdown 包裹、夹杂文字）。
- [x] 超时、网络错误处理：适配器抛出可分类异常，调用方可保持原数据不变。
- [x] `GET /api/v1/models` 列出可用模型及其能力。

### 1.3 前端 UI 框架
- [x] 将 `prototype/` 原型接入 FastAPI 静态文件服务，浏览器可直接访问。
- [x] 原型中的导航、弹窗、状态切换逻辑保持不变，作品库已按 API 接入并保留离线 fallback。
- [x] 前端 API 基路径 `/api/v1`，请求封装（json + error handling）。

### 1.4 作品库
- [x] 数据模型：`Story` 表（stage/idea_text/version/deleted_at），含软删除。
- [x] `GET /api/v1/works` — 列表接口（过滤软删除、返回阶段/进度/封面）。
- [x] `POST /api/v1/works` — 创建故事（`stage=idea`，空 idea_text）。
- [x] `DELETE /api/v1/works/{id}` — 软删除故事（需确认 token）。
- [x] `GET /api/v1/works/{id}` — 故事详情。
- [x] 前端接入：作品库页面从 API 获取列表（API 不可用时保留模拟 fallback），新建与删除调用 API。
- [x] 空状态、删除确认、创建后的 toast 反馈。

### Phase 1 验收
- [x] `py -3.13 -m alembic upgrade head` 从零建库（隔离 `phase1_smoke.db` 与 `phase1_server.db` 验证）。
- [x] `py -3.13 -m pytest -q` 全部通过：7 passed；覆盖 works CRUD、软删除、Idea 乐观锁、AI 配置校验、模型目录、JSON 容错、Grok 参数约束、Fake Adapter。
- [x] 浏览器真实验证：`http://127.0.0.1:8021/prototype/` 作品库空状态 → API 创建作品 → 进入 Idea；健康检查与 `/api/v1/works` 返回正常。

### Phase 1 交付证据（2026-08-11）

- 新工程基座位于 `app/`；旧实现（`app_v1_archived/`、`migrations/versions_v1_archived/`、`tests_v1_archived/`）已于 2026-08-14 清理，历史可从 Git 追溯。
- 新增 `openai>=1.60,<2` 依赖，使用 `README.md` 模型接入表规定的三个端点、模型 ID 与环境变量；真实最小调用结果：Agnes、DeepSeek、Grok 均成功。
- 原型作品库通过 `/api/v1/works`、`POST /works`、`DELETE /works/{id}` 工作；API 不可用时才回退到静态演示数据，未改变原型交互。
- 新增 `app/works/models.py`、`schemas.py`、`service.py`、`app/infrastructure/model_adapter.py`、`fake_adapter.py` 与 `tests/test_phase1.py`。
- 迁移环境改为读取应用 `DATABASE_URL`，新工程不再依赖旧多 head 数据库。

---

## Phase 2｜创意输入与 Story Concept（已完成 2026-08-11）

**目标：** 交付 Idea → Concept 纵向切片，验证 AI 生成与作者确认闭环。

- [x] Idea 保存与锁定：`PUT /api/v1/stories/{id}/idea`，仅 `stage=idea` 可写；概念生成后 stage 变为 `idea_locked`。
- [x] Story Concept 生成：`POST /api/v1/stories/{id}/generations`（action=generate_concept），携带 `ai_config_snapshot`。
- [x] Concept 编辑、字段级 Lock、重新生成与确认。
- [x] AI 生成设置：`PUT /api/v1/stories/{id}/ai-config`（model/temperature/reasoning_strength），`GET` 读取当前配置。
- [x] 前端接入：创意页 API 读写、概念页候选展示与确认、生成设置弹窗对接 API。
- [x] 书名自动生成：未命名作品确认 Concept 后自动生成书名（`generate_title` 任务，失败降级保留原名）；`PUT /api/v1/stories/{id}/title` 支持作者随时改名（乐观锁）。
- [x] 输入链消毒：移除前端 idea/概念页静态演示预填；Concept 生成服务对 `selling_points` 等字段做输出规范化（字符串→数组）；章节 fallback 改为基于创意的通用占位（不再硬编码示例故事）；生成/确认前前置校验。

### Phase 2 验收
- Idea 保存 409 锁定后不可写；Concept 候选不自动应用；Lock 字段不被生成覆写；生成设置保存后影响后续任务快照。
- 未命名作品确认 Concept 后书名由 AI 生成且可改；已命名作品不被自动覆盖；改名版本冲突返回 409。
- 演示/示例内容绝不进入模型输入链；模型输出字段结构不匹配时由服务端规范化，前端不残留静态候选。

---

## Phase 3｜Story Blueprint（已完成 2026-08-12）

**目标：** 交付 Blueprint 页面与双层状态数据（Baseline + Living State）。

- [x] Characters / World / Initial Timeline / Story Arc 的生成、编辑、Lock、确认。
- [x] 四类 Blueprint 工件独立追加版本，支持 `locked_paths` 和 `expected_version` 乐观锁。
- [x] Blueprint Baseline 与 Living State 独立版本及来源记录；四类 Baseline 确认时自动创建初始 Living State。
- [x] Living State 初始投影保存 `source_ref`、版本、`certainty=confirmed`、`context_policy=always` 和 `temporal_scope=story_start`。
- [x] 前端接入：蓝图页面 API 读取、分类切换、候选生成、确认状态与 Living State 数据基础映射；保留原型详细视图与履历入口。

### Phase 2 验收
- Bible + Arc 均 confirmed 后才可 `blueprint_confirmed`；Living State 仅接受 confirmed 条目；Entity Lock 阻止生成覆写。
Blueprint 验收：Concept 未确认时生成返回 409；四类 Baseline 候选生成并可独立编辑；版本冲突和重复确认返回 409；确认后 Story 进入 `blueprint_confirmed` 并创建 `living_state` confirmed 投影。已完成 9 项 pytest；真实 API 验证 Concept → Blueprint 返回 4 个分类工件成功。
---

## Phase 4｜Chapter Plan 与逐章激活（已完成 2026-08-12）

**目标：** 将 Blueprint 拆分为章节卡片并建立激活规则。

- [x] AI 生成 Chapter Card 列表（title/goal/summary/characters/arc_role）。
- [x] Chapter 1 = fixed + active；后序 = outline + locked。
- [x] `access_status` 服务端强制：locked 章节不可规划或进入工作台（409）。
- [x] 前端接入：章节卡片页 API 读取、章节雏形生成、进入工作台入口按钮、锁定提示。

### Phase 4 验收

已完成 10 项 pytest；Phase 4 独立迁移成功；离线状态机验证首章 active、后序章节 locked、锁定章节编辑返回 409。真实模型链路已验证 Concept → Blueprint → Chapter Plan API，Chapter Plan 服务支持模型输出数组与 fallback，章节生成任务保存模型配置快照。

---

## Phase 5｜Chapter Workspace：Context、Scene 与 Beat（已完成 2026-08-13）

**目标：** 在唯一工作台页面完成章节级规划。

- [x] State Snapshot 构建（Character/World/Timeline 三域，无未来信息）。`state_snapshots` 表；激活章节首次读取 Context 时从已确认 Living State 投影三域快照并计算 `state_hash`；Phase 6 将折叠已确认 Delta。
- [x] Chapter Events 编辑（planned_result 与 actual_result 分离）。`chapter_events` 表；创建/编辑/删除事件，乐观锁；planned 与 actual 结果独立维护。
- [x] Scene Plan / Beat Plan 的创建、排序与顺序约束。`scenes`/`beats` 表；AI 生成场景计划（generate_scene_plan）与节拍计划（generate_beat_plan），失败回退到基于章节目标的占位；仅最小未完成 ordinal 置为 `available`，其余 `planned`；锁定章节编辑返回 409。
- [x] 前端接入：工作台左侧 Chapter→Scene 两级、Scene 描述与 Beat Cards、窄状态栏与全貌状态覆盖面板。工作台从 `GET /chapters/{id}/context` 加载真实数据；场景列表、场景描述（地点/时间/POV/目标/冲突/关键事件/结果）、Beat Cards、生成场景计划与生成节拍计划按钮；加载中占位而非演示数据；标题动态更新为当前章节。

### Phase 5 验收

- 7 项 pytest（`tests/test_phase5.py`）通过：Snapshot 三域构建、Event planned/actual 分离与乐观锁、Scene 计划生成与顺序约束、Beat 计划生成、Scene/Beat 更新版本冲突 409、锁定章节只读、Event 删除。
- 迁移 `20260813_0004_chapter_workspace` 从空库升级成功，四张表及唯一约束可验证。
- 真实模型链路：`冬夜同行` Chapter 01 Context 返回三域 Snapshot（characters/world/timeline + state_hash）；生成 4 个场景计划（第 1 个 available）；场景 1 生成 6 个真实 Beat，场景 4 重新生成 5 个真实 Beat。
- 浏览器实测：工作台显示真实章节标题「边缘的注视」、4 个场景与 Beat Cards；场景切换、生成场景计划、生成节拍计划按钮均工作，toast 反馈正常。

---

## Phase 6｜正文生成、State Delta 与 Next Chapter（已完成 2026-08-13）

**目标：** 完成章节级正文生成、状态更新与下一章激活。

- [x] Beat 级 Markdown 版本（append-only）、应用与单 Beat 重生成。`prose_versions` 表；生成创建 candidate 版本、应用创建 applied 新版本（parent 链）、重新生成创建新候选且历史保留；`beat_id+version` 唯一约束。
- [x] 顺序生成执行器：从首个未完成 Beat 开始，支持「生成当前 Scene」与「完成本章剩余」。`generate_scene` / `generate_chapter_remaining` / `regenerate_beat`；已有部分正文时从最后一个未完成 Beat 继续。
- [x] Beat/Scene 检查点：proposed 候选 Delta、一致性检查。生成后自动创建 beat 级 `state_deltas`（proposed）并运行 `consistency_issues` 检查（prose_too_short / placeholder_content 等规则）。
- [x] Chapter Delta 合并、检查与作者确认。`build_chapter_delta` 合并 beat delta；`POST /deltas/confirm` 作者确认后更新 Living State（记录 `last_confirmed_chapter` 与 `confirmed_deltas`）、激活 ordinal + 1。
- [x] 历史章节变更后的 stale 标记与按序重算。`mark_subsequent_stale` 将后续章节 Snapshot 标记 stale 并记录 `stale_reason`。

### Phase 6 验收

- 7 项 pytest（`tests/test_phase6.py`）通过：候选正文生成、apply append-only 与乐观锁 409、章节剩余生成、重生成不覆盖、一致性检查记录、Delta 确认激活下一章 + Living State 更新、stale 标记。
- 迁移 `20260813_0005_prose_deltas` 空库往返（upgrade→downgrade→upgrade）成功，三张表约束可验证。
- 真实模型链路：`冬夜同行` Chapter 01 的 6 个 Beat 全部生成真实正文（猫视角初遇巷口描写）并应用；Scene 1 状态 completed；确认 Chapter Delta 后第 1 章完成、第 2 章「风雨夜的同盟」激活。
- 浏览器实测：Beat 卡显示候选正文、「应用候选正文」按钮、应用后标记已完成；Scene 1 完成后出现「Chapter Delta 就绪」确认区；确认后工作台切换到 Chapter 02 并提示「第 2 章已激活」。
- 修复：Phase 6 迁移最初未应用到主库（终端残留 `DATABASE_URL` 指向临时库），显式指向 `novel_ignite.db` 后升级完成；前端静态资源 bump 为 `v20260813b` 强制刷新缓存。

---

## 横向质量门槛（全 Phase 持续）

- 所有 schema 变更通过 Alembic 迁移；持久化行为覆盖迁移和服务测试。
- API 使用 Pydantic DTO；页面不访问 ORM 或模型服务。
- 生成任务记录参数快照、上下文引用与输出摘要；日志不记录正文/密钥全文。
- 版本冲突返回 409；任何失败不得覆盖作者原文。
- UI 覆盖 loading / failed / empty / locked / stale / conflict 状态。
- 桌面与窄屏均可完成完整闭环。
- **Phase 4 后新增 E2E 测试套件**（`tests/e2e/`）：Playwright 驱动的浏览器级端到端测试，覆盖完整创作流程（创意→概念→蓝图→章节），在每次大更新后必须运行。

---

## 当前下一步

**MVP 完成定义已达成**（作品库 → 创意 → 概念 → 蓝图 → 章节 → 工作台 → 正文 → Delta 确认 → 下一章完整闭环）。后续可选项：
1. Phase 6 增强：AI 驱动的 Delta 提取与一致性检查（当前为确定性占位规则）；Scene 完成时生成 Scene Summary 并修订后续计划。
2. 正文编辑：工作台内 Markdown 编辑 + 应用（作者可直接修改候选后应用）。
3. E2E 全流程测试补全：`tests/e2e/test_full_flow.py` 时序问题修复，覆盖新工作台正文流程。
4. README 与架构文档同步 Phase 5/6 真实范围。

## 测试套件

| 类型 | 文件 | 数量 | 状态 |
|------|------|------|------|
| 后端单元测试 | `tests/test_phase1.py` | 24 | ✅ 全部通过 |
| 后端单元测试 | `tests/test_phase5.py` | 7 | ✅ 全部通过 |
| 后端单元测试 | `tests/test_phase6.py` | 8 | ✅ 全部通过 |
| E2E 冒烟测试 | `tests/e2e/test_smoke.py` | 3 | ✅ 全部通过 |
| E2E 全流程测试 | `tests/e2e/test_full_flow.py` | 14 | ⏳ 待优化（pytest-playwright 时序问题） |

### 运行方式
```bash
# 后端单元测试
py -3.13 -m pytest tests/test_phase1.py -v

# E2E 冒烟测试（快速）
py -3.13 -m pytest tests/e2e/test_smoke.py -v

# E2E 全流程测试
py -3.13 -m pytest tests/e2e/test_full_flow.py -v

# 调试模式（显示浏览器）
py -3.13 -m pytest tests/e2e -v --headed --slowmo 300
```

### 前置依赖
```bash
pip install -e ".[e2e]"
playwright install chromium
```

## 变更日志

- 2026-08-11：基于 `prototype/` 交互原型重建 v2 开发计划。将旧实现归档为 `app_v1_archived/`。Phase 1 聚焦基础框架、大模型适配、前端框架与作品库四块同步交付。后续 Phase 按 Idea → Concept → Blueprint → Chapter Plan → Chapter Workspace → Next Chapter 功能递进。
- 2026-08-11：完成 Phase 1：新 app 基座、SQLite/Alembic、作品库 CRUD、AI 配置、三模型 OpenAI 兼容适配器、Fake Adapter、原型 API 接入；7 项测试通过，三种真实模型最小调用成功，浏览器完成 API 作品库 → Idea 路径验证。
- 2026-08-11：完成 Phase 2：新增 `story_artifacts`、`generation_tasks` 与 Concept 候选服务；实现 Idea 锁定、Concept 生成/编辑/确认、乐观锁、重复确认 409；原型创意/概念页接入真实 API；8 项测试通过，三模型真实 Concept 生成与浏览器确认路径成功。
- 2026-08-12：完成 Phase 3：Blueprint 四分类 Baseline 工件、候选生成/编辑/Lock/确认 API；确认后自动创建 Living State 初始投影；原型蓝图页接入真实读取/生成/确认；9 项测试通过，真实 API Concept → Blueprint 成功返回 4 个分类工件。
- 2026-08-12：完成 Phase 4：新增 `chapters` 表、Chapter Plan 生成服务与逐章激活规则；首章 `fixed + active`、后续 `outline + locked`；原型章节页接入真实列表/生成 API；10 项测试通过，锁定章节编辑返回 409，README 已同步当前真实范围。
- 2026-08-12：概念确认后自动生成书名：未命名作品确认 Concept 时由配置模型生成标题（`generate_title` 任务，失败降级保留原名，已命名作品不覆盖）；新增 `PUT /api/v1/stories/{id}/title` 支持作者随时改名并同步顶部与作品库；原型顶部书名增加 ✎ 编辑入口。13 项 pytest 通过；真实模型「橘猫治愈系」概念确认后生成《听心猫》，改名《听心猫与失语少年》后作品库同步。
- 2026-08-12：定位并修复「模型持续输出林墨演示设定」的根因——污染来自前端静态演示预填，而非模型。真实链路：概念页静态表单预填林墨卖点 → LLM 输出的 `selling_points` 为字符串（非数组）→ 前端 `Array.isArray` 判断跳过覆盖 → 静态林墨卖点残留 → 确认时作为作者内容保存。修复：① 清除 idea/概念页静态演示预填；② 概念服务对输出做 `_normalize_concept_payload`（selling_points 字符串→数组）并强化 prompt 约束；③ 章节 fallback 改为基于创意的通用占位；④ 前端 `applyConceptPayload` 兼容字符串卖点并总是覆盖/清空；⑤ 生成/确认前置校验（idea 非空、确认前需先生成）。另修复生成前 idea 防抖未落库导致 422 的竞态。存量数据核查无污染；15 项 pytest 通过；浏览器实测橘猫概念卖点为 5 条干净数组。
- 2026-08-12：蓝图渲染只显示第一个条目的 bug 修复：`blueprintPayloadToUi` 由 `entries[0]` 改为遍历全部条目，蓝图 tab 计数改为动态（人物 4/世界 4/时间线 6/弧 5 等真实值），无数据分类显示占位；修复《寒夜同行》人物页只显示雪团（猫）而丢失木木（狗）的问题。
- 2026-08-12：按官方文档重写三模型思考/推理参数传递（`model_adapter.py`）：Agnes 升级 2.0→2.5（`agnes-2.5-flash`），思考经 `extra_body.chat_template_kwargs.enable_thinking` 开启（low 关闭）；DeepSeek 思考模式默认开启，`extra_body.thinking={type:enabled}` + 顶层 `reasoning_effort`（映射 medium→high）；Grok 推理内置无法关闭，顶层 `reasoning_effort`。修正此前把 `reasoning_effort` 误放入 `extra_body` 导致推理参数可能无效的问题。真实调用验证：三模型均返回完整 JSON 概念；前端/README/接入文档同步升级 Agnes 2.5。18 项 pytest 通过。
- 2026-08-12：各模型最大输出按官方上限设置：`ModelSpec.max_output_tokens`（Agnes 2.5 65.5K / DeepSeek v4-flash 384K / Grok 4.5 500K），生成调用不传 `max_tokens` 时自动使用官方上限；蓝图/章节生成移除 8192 硬编码上限。真实调用验证三模型均接受官方最大值。20 项 pytest 通过。
- 2026-08-13：① 确认概念后自动生成蓝图候选（前端在 confirm 成功后调用 blueprint/generations），无需再点「生成候选」；② 延迟修复：前端 `apiRequest` 增加 AbortController 超时（160s）并在超时/失败时快速 toast、`openConfig` 先用本地缓存立即打开弹窗再异步刷新、模型超时统一为 150s、SQLite 启用 WAL + busy_timeout(30s) 消除并发写锁 500；③ 清理根目录调试残留（`phase1_local.db`、`phase3_debug.db-journal`、`dist/`）并重写 `scripts/verify_models.py` 适配当前架构；④ 建立可观测性体系：`app/infrastructure/observability.py`（结构化 JSONL 日志 + 内存指标）、HTTP 中间件记录请求耗时/状态与请求异常、模型适配器内嵌上报（模型/耗时/token/状态/错误类型，生成服务标注业务 action）、`GET /metrics` 指标端点、`logs/` 目录（gitignore 排除）。22 项 pytest 通过；浏览器实测「诗人」概念确认后自动生成《忘名诗》与四分类蓝图，并发 idea 保存全部 200。
- 2026-08-13：可观测性增强：日志按大小轮转（默认 5MB，保留 5 份，`NOVEL_LOG_DIR`/`NOVEL_MAX_LOG_BYTES` 可覆盖）；新增 `scripts/analyze_metrics.py` 分析脚本（按 action/模型汇总成功率、平均/最大耗时、token、错误类型、最慢请求/生成，`--json` 结构化输出）；测试通过 `tests/conftest.py` 将日志隔离到临时目录，不再污染 `logs/`。22 项 pytest 通过，报表实测可定位 blueprint 生成 22s 慢路径与 Agnes TimeoutError。
- 2026-08-13：修复「概念生成后内容为空、重新生成无效」：① 根因是 `novel_ignite.db` 损坏（文件被覆盖为源码文本，怀疑 WAL 辅助文件被误删所致）——已重建数据库，并将 SQLite 由 WAL 改回默认 journal（避免 `-wal/-shm` 辅助文件误删再导致损坏，保留 busy_timeout 30s 缓解并发锁）；② 概念页「↻ 重新生成」按钮此前未绑定事件——抽出 `generateConcept()` 复用于「AI生成概念」与「重新生成」；③ 前端静态资源缓存导致新代码不生效（app.js 固定版本号）——bump 为 `v20260813` 并在中间件对 `/prototype/` 设置 `Cache-Control: no-store`；④ 概念候选版本号动态显示。浏览器实测生成内容完整、重新生成后更新为 v2 新内容。22 项 pytest 通过。
- 2026-08-13：修复「确认蓝图后章节为空、蓝图页找不到生成章节入口」：① 根因是章节生成服务对模型输出要求必须是数组，而 Agnes 返回 `{"chapters": [...]}` 包装对象导致 `ValueError` → 502 —— 新增 `_normalize_chapter_plan`（兼容对象包装、字段容错），非数组时回退到基于创意的占位，不再 502；② 确认蓝图后自动生成章节雏形（与「确认概念→自动蓝图」一致），失败降级提示并保留手动按钮；③ 蓝图已确认时右上角显示「进入章节规划」按钮（`#to-chapters`），解决确认后无入口的问题。浏览器实测「街角的我们」手动生成 6 章成功、新作品确认蓝图后自动生成 6 章（第 1 章激活）。24 项 pytest 通过。
- 2026-08-13：建立 E2E 端到端测试套件（`tests/e2e/`）。使用 Playwright 驱动浏览器，覆盖完整创作流程：① `test_smoke.py` — CI 快速冒烟：后端健康检查、原型页可访问、新建按钮可见；② `test_full_flow.py` — 全流程验证：作品卡片显示、创意填写、概念生成与确认、蓝图生成与确认、章节规划、工作台跳转、弹窗交互、步骤条导航、面包屑更新。共 12 个 E2E 测试用例。`pyproject.toml` 新增 `e2e` 可选依赖。运行方式：`pytest tests/e2e -v`（headless）或 `--headed --slowmo 300`（调试）。
- 2026-08-13：完成 Phase 5（Chapter Workspace）：① 修复 `app/works/blueprint_service.py` 文件损坏（含 241 个 NUL 字节，从 git HEAD 恢复）；② 新增 `state_snapshots`、`chapter_events`、`scenes`、`beats` 四张表与迁移 `20260813_0004_chapter_workspace`；③ `app/planning/workspace_service.py` 实现 Snapshot 三域构建（无未来信息）、Chapter Event planned/actual 分离编辑、Scene/Beat 计划管理（顺序约束 + 乐观锁）、AI 场景/节拍计划生成（失败回退占位）；④ 新增 API：`GET /chapters/{id}/context`、`POST /chapters/{id}/generations`（generate_scene_plan）、`POST /chapters/{id}/scenes/{sid}/generations`（generate_beat_plan）、Events/Scenes/Beats 的 CRUD；⑤ 前端工作台接入真实 API（加载占位、场景列表/描述/Beat Cards、生成场景/节拍计划按钮、标题动态更新）；⑥ 将 `client` fixture 上移到共享 `tests/conftest.py`。7 项新 pytest 通过（总计 31）；真实模型验证「冬夜同行」Chapter 01 生成 4 个场景与真实 Beat，浏览器端场景切换与生成按钮均工作。
- 2026-08-13：完成 Phase 6（正文生成、State Delta 与 Next Chapter）：① 新增 `prose_versions`、`state_deltas`、`consistency_issues` 三张表与迁移 `20260813_0005_prose_deltas`；② `app/planning/writing_service.py` 实现 append-only 正文版本（candidate/applied/parent 链）、顺序生成执行器（generate_scene / generate_chapter_remaining / regenerate_beat）、Beat 检查点（proposed Delta + 一致性检查）、Chapter Delta 合并与作者确认（更新 Living State + 激活下一章）、stale 标记；③ 新增 API：`GET/POST .../beats/{id}/prose`、`POST .../beats/{id}/prose-versions`、`GET .../deltas`、`POST .../deltas/confirm`、`GET .../issues`，`generations` 扩展 generate_scene / generate_chapter_remaining / regenerate_beat；④ 前端工作台接入：Beat 卡显示候选正文与「应用候选正文」按钮、场景生成/完成本章剩余按钮、Scene 全 Beat 应用后显示「Chapter Delta 就绪」确认区、确认后自动切换到下一章；⑤ 修复：Phase 6 迁移因终端残留 `DATABASE_URL` 未应用到主库（显式指向 `novel_ignite.db` 后完成），前端静态资源 bump `v20260813b`。7 项新 pytest 通过（总计 41）；真实模型验证「冬夜同行」Chapter 01 六个 Beat 真实正文生成并应用、Scene 1 completed、确认 Delta 后第 2 章激活，浏览器端完整闭环工作。
- 2026-08-14：修复两个问题：① **已完成章节被显示为「未激活 · 雏形」**——前端 `renderChaptersFromApi` 只区分 `active` 与其余状态，导致 `completed` 章节错误渲染；现区分三种状态：active「可进入 · 当前章」、completed「✓ 已完成」、locked「未激活 · 雏形」，章节概览同时显示「已完成 N 章」。② **生成内容自动接受**——按作者要求，场景/节拍/正文生成默认自动保存与接受：`_generate_beat` 生成的正文直接以 `applied` 状态落库（append-only 版本历史保留，可随时「重新生成」创建新版本），beat 直接标记 `applied`，不再需要人工点击「应用候选正文」；`regenerate_beat` 放宽为可对已应用/已完成 beat 重生成。前端移除「应用候选正文」按钮，文案同步「已生成并自动应用」；静态资源 bump `v20260814`。同步更新测试 `test_phase6.py`（generate_scene 断言 applied、regenerate 断言新版本 applied）。41 项 pytest 通过；浏览器实测第 2 章「风雨夜的同盟」Scene 1 五个 Beat 一键生成即全部自动应用、Scene 变 completed 并出现 Delta 确认区。
- 2026-08-14：修复「查看已完成章节」与「等待蓝图确认」两个问题：① **「查看已完成章节」按钮此前仅显示 toast 无实际跳转**——现点击后进入该已完成章节的只读工作台：标题标注「（已完成）」，正文/场景/Beat 完整展示（「已应用 vX」版本标记），所有生成/编辑/确认按钮隐藏（「一键生成整个章节」禁用），仅可浏览历史；步骤条「工作台」与「进入当前章节工作台」始终回到当前激活章节。② **「等待蓝图确认」状态显示错误**——`#chapter-plan-note` 仅在章节为空时更新，有章节时残留 HTML 默认值「等待蓝图确认」与实际（已生成 6 章）矛盾；现 `renderChaptersFromApi` 同步更新为「已生成 · 第 X 章已激活」。前端静态资源 bump `v20260814b`。41 项 pytest 通过；浏览器实测「寒冬归途」章节页 note 显示「已生成 · 第 3 章已激活」，点击 CHAPTER 01「查看已完成章节」进入只读工作台展示第 1 章正文。
- 2026-08-14：修复「一键生成整个章节」按钮：此前该按钮（`#complete-chapter`）仍绑定旧 `simulateGeneration` 模拟逻辑，点击提示「模拟执行已暂停在作者确认点」而无法真实生成。现改为真实完整流程：自动确保场景计划 → 逐场景确保节拍计划 → **逐场景生成正文并自动应用**（每个场景独立请求，超时 600s，避免整章单请求超过前端 160s 超时被 AbortController 中止）；任一环节超时/失败后自动刷新显示服务端实际进度，可再次点击继续（幂等：已完成场景跳过）。同时为「生成整个 Scene 正文」「生成 Beat 正文」「完成本章剩余」设置更大超时（600s）。静态资源 bump `v20260814d`。41 项 pytest 通过；浏览器实测「寒冬归途」第 3 章点击后逐场景发出 4 个生成请求、toast「本章正文已全部生成并应用，请确认 Chapter Delta 后进入下一章」，4 个场景全部 completed 并出现 Delta 确认区。
- 2026-08-14：修复「蓝图 Living State 与工作台状态面板显示演示假数据」：① **蓝图 Living State**——`blueprintData.living` 原为硬编码的「林墨/旧港鉴定所/记忆监管局」演示数据，且 `loadBlueprintForCurrentStory` 从不加载真实 `living_state`；新增 `livingPayloadToUi` 从真实 artifact 的 `payload.domains`（characters/world/timeline）投影三个领域卡片（角色/世界/时间线状态），蓝图加载时同步填充。② **工作台右侧状态面板（status-rail）**——原为 index.html 静态「有效 · Chapter 01 入口 / Scene 1 已完成 · 3 个 Beat / 2 条 Delta / 1 条提醒」；现 `loadWorkspaceContext` 并行获取 `/deltas` 与 `/issues`，新增 `renderWorkspaceStatus` 用真实数据更新 Snapshot 状态（章节号、valid/stale）、Scene 进度（done/total 场景与 Beat）、proposed Delta 计数、open 问题计数。③ **全局状态弹窗（state-modal）**——由静态林墨内容改为从 `context.snapshot.state`（三域）+ `context.events` 重建角色/世界/时间线/Chapter Events，底部标签显示真实 Delta 状态。静态资源 bump `v20260815`。41 项 pytest 通过；浏览器实测「寒冬归途」蓝图 Living State 显示真实设定（墨墨黑猫/阿黄黄狗/面包店老板/城市旧街区），工作台状态面板显示「有效 · Chapter 03 入口 / 已完成 4/4 场景 / 20 条 · 待确认」，全局状态弹窗展示真实角色与事件。
- 2026-08-14：修复「Living State 更新履历永远只有 v1」：**根因**——旧 `confirm_chapter_delta` 确认章节时只原地改写 `living.payload` 元数据（`last_confirmed_chapter`/`confirmed_deltas`），从不创建新 artifact 版本，也从不把 Delta 变更投影进三个领域，因此无论确认多少章，Living State 恒为 v1、履历恒为 1 条（实测「寒冬归途」已确认 2 章但履历仍仅 v1）。**修复**——① `confirm_chapter_delta` 改为创建**新的 Living State 版本**（version+1，status confirmed），新增 `_apply_changes_to_domains` 将本章 Delta 变更投影进 domains（character/world 变更合并同名条目或追加；timeline 事件聚合为「第 N 章 · 事件推进」条目），历史版本保留不可变。② 新增端点 `GET /stories/{sid}/living-state/history`（`list_living_state_history`，按版本倒序）供履历弹窗追溯。③ **顺带修复数据缺口**：`apply_beat_prose`（作者手工应用正文）此前不生成 Delta，只有 AI 生成的 `_generate_beat` 才调用 `create_beat_delta`，导致手工应用章节确认时 Chapter Delta 为空、无法投影状态；现手工应用正文同样走 proposed beat delta + 一致性检查。④ 前端 `openHistory` 对 living 分类异步拉取版本历史，展示每条版本（初始投影 / 第 N 章 Delta 确认）与三领域条目计数。静态资源 bump `v20260815b`。新增测试 `test_living_state_versions_increment_per_confirmed_chapter`（确认 2 章后 v3、history 返回 [3,2,1]、timeline 含两章事件推进）。42 项 pytest 通过；浏览器实测履历弹窗显示「v1 初始投影（蓝图确认）· 角色 4 / 世界 4 / 时间线 5 条」。注意：旧逻辑已确认的章节（如「寒冬归途」第 1-2 章）未生成对应 Living State 版本，如需补建需另行处理。
- 2026-08-14：修复「全局故事状态弹窗仍显示林墨假数据」：**根因**——`index.html` 中 `#state-modal` 的静态 HTML 硬编码了「林墨/旧港鉴定所/乔岚/记忆复制规则/12 年前记忆商品化」演示数据与静态 eyebrow「LIVING STATE · CHAPTER 01 ENTRY」、静态 foot「2 条 Delta 候选」；旧版 app.js（v20260813 等）不含 `renderWorkspaceStatus`，因此旧页面打开弹窗直接显示这段静态假数据（实测 8035/8036/8037 旧实例 + 旧 app.js 页面复现）。**修复**——① `index.html` 删除 `#state-modal` 内全部演示内容，改为中性占位（「正在加载故事状态…」+ eyebrow「LIVING STATE · 当前章节入口」），确保任何情况下不显示假数据，内容只由 JS 填充。② `renderWorkspaceStatus` 补充 eyebrow 动态化（显示真实入口章节号，如 `LIVING STATE · CHAPTER 04 ENTRY`）。③ 修复时间线「第 N 章 · 事件推进」渲染成 `[object Object]` 的缺陷：新增 `fmt` 格式化函数，将对象/对象数组字段（timeline events）格式化为 `event：…，scene：…，note：…` 可读文本，角色/世界/时间线字段统一走 `fmt`。静态资源 bump `v20260815c`。42 项 pytest 通过；浏览器实测（8000 端口）state-modal eyebrow 显示真实 `CHAPTER 04 ENTRY`、时间线事件显示明细、无林墨数据、foot 显示真实 Delta 计数。
- 2026-08-14：清理归档代码与文档：删除 `app_v1_archived/`（旧 v1 实现）、`tests_v1_archived/`（旧测试）、`migrations/versions_v1_archived/`（旧迁移）、`docs/development-plan-v1-archived.md`（旧开发计划）、`docs/LLM接入临时参考.md`（内容已并入 README 模型接入表）。同步更新 README（可操作范围扩展至 Phase 6、API 列表补充 Chapter Workspace / Delta / Issue / Living State 历史端点、测试数更新为 42、目录移除归档行）、`docs/development-plan.md` Phase 1 交付证据与变更日志、`docs/technical-architecture.html` 页脚（归档引用改为「已清理，Git 历史可追溯」）。本地旧库备份 `novel_ignite_v1_archived.db` 保留（gitignore 排除，不提交）。
- 2026-08-14：前端主界面挂载路径由 `/prototype/` 移至根路径 `/`：`app/main.py` 中 `app.mount("/prototype", …)` 改为 `app.mount("/", …)`（注意 mount 必须注册在 `/health`、`/metrics` 之后，避免根路径挂载拦截 API/健康检查；`/docs`、`/openapi.json` 由 FastAPI 初始化注册不受影响），no-store 缓存中间件由 `/prototype/` 前缀改为「非 `/api/` 路径」全部 no-store；E2E 测试 13 处 URL 由 `…/prototype/` 改为 `…/`；README 访问地址更新为 `http://127.0.0.1:8000/`。前端文件仍组织在 `prototype/` 目录（资源引用为相对路径、API 为绝对路径，均与挂载路径解耦，无需改动）。浏览器实测根路径直接打开作品库、`/health`、`/metrics`、`/docs`、`/api/v1/works` 均 200，E2E 冒烟 3 项通过。
