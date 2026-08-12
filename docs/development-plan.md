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

- 新工程基座位于 `app/`，旧实现已归档为 `app_v1_archived/`；旧迁移归档为 `migrations/versions_v1_archived/`，旧测试归档为 `tests_v1_archived/`。
- 新增 `openai>=1.60,<2` 依赖，使用 `docs/LLM接入临时参考.md` 规定的三个端点、模型 ID 与环境变量；真实最小调用结果：Agnes、DeepSeek、Grok 均成功。
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

### Phase 2 验收
- Idea 保存 409 锁定后不可写；Concept 候选不自动应用；Lock 字段不被生成覆写；生成设置保存后影响后续任务快照。
- 未命名作品确认 Concept 后书名由 AI 生成且可改；已命名作品不被自动覆盖；改名版本冲突返回 409。

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

## Phase 5｜Chapter Workspace：Context、Scene 与 Beat

**目标：** 在唯一工作台页面完成章节级规划。

- [ ] State Snapshot 构建（Character/World/Timeline 三域，无未来信息）。
- [ ] Chapter Events 编辑（planned_result 与 actual_result 分离）。
- [ ] Scene Plan / Beat Plan 的创建、排序与顺序约束。
- [ ] 前端接入：工作台左侧 Chapter→Scene 两级、Scene 描述与 Beat Cards、窄状态栏与全貌状态覆盖面板。

---

## Phase 6｜正文生成、State Delta 与 Next Chapter

**目标：** 完成章节级正文生成、状态更新与下一章激活。

- [ ] Beat 级 Markdown 版本（append-only）、应用与单 Beat 重生成。
- [ ] 顺序生成执行器：从首个未完成 Beat 开始，支持「生成当前 Scene」与「完成本章剩余」。
- [ ] Beat/Scene 检查点：proposed 候选 Delta、一致性检查。
- [ ] Chapter Delta 合并、检查与作者确认。
- [ ] 确认后更新 Story State / Living State；仅激活 ordinal + 1。
- [ ] 历史章节变更后的 stale 标记与按序重算。

---

## 横向质量门槛（全 Phase 持续）

- 所有 schema 变更通过 Alembic 迁移；持久化行为覆盖迁移和服务测试。
- API 使用 Pydantic DTO；页面不访问 ORM 或模型服务。
- 生成任务记录参数快照、上下文引用与输出摘要；日志不记录正文/密钥全文。
- 版本冲突返回 409；任何失败不得覆盖作者原文。
- UI 覆盖 loading / failed / empty / locked / stale / conflict 状态。
- 桌面与窄屏均可完成完整闭环。

---

## 当前下一步

1. Phase 5.1：实现 Chapter Context 与 State Snapshot 三域模型。
2. Phase 5.2：实现 Chapter Events、Scene Plan、Beat Plan 与顺序约束。
3. Phase 5.3：接入唯一 Chapter Workspace 的 Chapter → Scene → Beat 交互。
4. Phase 5.4：完成 Snapshot 未来信息过滤与真实模型章节上下文回归。

## 变更日志

- 2026-08-11：基于 `prototype/` 交互原型重建 v2 开发计划。将旧实现归档为 `app_v1_archived/`。Phase 1 聚焦基础框架、大模型适配、前端框架与作品库四块同步交付。后续 Phase 按 Idea → Concept → Blueprint → Chapter Plan → Chapter Workspace → Next Chapter 功能递进。
- 2026-08-11：完成 Phase 1：新 app 基座、SQLite/Alembic、作品库 CRUD、AI 配置、三模型 OpenAI 兼容适配器、Fake Adapter、原型 API 接入；7 项测试通过，三种真实模型最小调用成功，浏览器完成 API 作品库 → Idea 路径验证。
- 2026-08-11：完成 Phase 2：新增 `story_artifacts`、`generation_tasks` 与 Concept 候选服务；实现 Idea 锁定、Concept 生成/编辑/确认、乐观锁、重复确认 409；原型创意/概念页接入真实 API；8 项测试通过，三模型真实 Concept 生成与浏览器确认路径成功。
- 2026-08-12：完成 Phase 3：Blueprint 四分类 Baseline 工件、候选生成/编辑/Lock/确认 API；确认后自动创建 Living State 初始投影；原型蓝图页接入真实读取/生成/确认；9 项测试通过，真实 API Concept → Blueprint 成功返回 4 个分类工件。
- 2026-08-12：完成 Phase 4：新增 `chapters` 表、Chapter Plan 生成服务与逐章激活规则；首章 `fixed + active`、后续 `outline + locked`；原型章节页接入真实列表/生成 API；10 项测试通过，锁定章节编辑返回 409，README 已同步当前真实范围。
- 2026-08-12：概念确认后自动生成书名：未命名作品确认 Concept 时由配置模型生成标题（`generate_title` 任务，失败降级保留原名，已命名作品不覆盖）；新增 `PUT /api/v1/stories/{id}/title` 支持作者随时改名并同步顶部与作品库；原型顶部书名增加 ✎ 编辑入口。13 项 pytest 通过；真实模型「橘猫治愈系」概念确认后生成《听心猫》，改名《听心猫与失语少年》后作品库同步。
