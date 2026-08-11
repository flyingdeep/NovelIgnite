# Novel Ignite 开发计划

> 产品需求事实来源：`../NOVEL_IGNITE_需求文档_V2.md`  
> 技术实现事实来源：`technical-architecture.html`  
> 产品流程与界面事实来源：`ui-design.html`

## 当前阶段：Phase 4｜Chapter Workspace：章节规划与写作一体化（待开始）

> **2026-08-11 产品重构裁决：** 本产品不是 JSON/后台管理工具，而是让作者从创意逐步完成小说策划与连续创作的易上手 AI 工具。页面必须严格遵循 `Idea → Concept → Blueprint → Chapter Plan → Chapter Workspace` 五步流程；每步只呈现该步的作者任务、候选、确认与清晰的下一步。确认 Blueprint 后不能停在编辑页，必须进入 Chapter Plan；进入章节后规划、生成与状态都在唯一的 Chapter Workspace 中完成。

## 产品交付方式（重构后）

1. **步骤隔离，不堆后台表单。** Idea、Concept、Blueprint、Chapter Plan 是独立的作者步骤；Chapter Workspace 是唯一章节页，不再拆 Chapter Planning / Writing 页面。
2. **作者看到结构化内容，而非原始 JSON。** JSON 仅作为开发/兼容的底层格式；正式交互按 Concept 字段、Blueprint 分类、Chapter Card、Scene、Beat Card 呈现。
3. **每个 Phase 必须交付垂直切片。** 数据迁移、领域服务、Pydantic API、前端交互、失败/空/锁定状态、pytest 与浏览器回归缺一不可。
4. **真实模型是验收的一部分。** 所有包含“生成”的 Phase，至少以一项可选真实模型完成一次成功路径；测试仍使用 fake adapter 保持可复现。
5. **以可继续创作为完成标准。** “API 存在”或“JSON 可提交”不能视作产品完成；作者必须从当前步骤看见并能进入下一步骤。

| 项目 | 状态 | 验收证据 |
|---|---|---|
| 需求与 Review 对齐 | 已完成（2026-08-11 重新校准） | 主流程为 Idea → Concept → Blueprint → Chapter Plan → Chapter Workspace → Next Chapter；章节规划与写作必须合并于唯一 Workspace。|
| 技术实现规范 | 已完成 | 定义 Blueprint 双层结构、逐章激活、Scene / Beat 顺序生成、检查点、状态更新、数据和 API 约束。|
| UI 设计规范 | 已完成 | 统一五步 Idea → Concept → Blueprint → Chapter Plan → Chapter Workspace 导航；单页章节工作台、Chapter → Scene 两级列表、Beat 卡片和状态覆盖层。|
| MVP 工程骨架 | 已完成 | Python 3.13 环境下已建立 FastAPI、SQLite、SQLAlchemy、Alembic、Pydantic 与 pytest 基础结构；初始迁移已验证。|
| 五步作者流程 | 进行中 | 已交付独立 Idea / Concept / Blueprint / Chapter Plan 与 active Chapter Workspace 入口；Context、Events、Scene、Beat、正文和 Delta 将在 Phase 4–6 完成。|

## MVP 完成定义

用户可以从 Idea 生成并确认 Story Concept 和 Story Blueprint；系统据此生成章节卡片，首次仅激活第一章。作者可在当前章节中确认 Chapter Context、Events、Scene Plan 和 Beat Plan，并按顺序生成单个 Scene 或本章剩余内容。每个 Beat、Scene、Chapter 完成后系统执行一致性与状态更新检查；Chapter Delta 经作者确认后更新 Story State 和 Blueprint Living State，并只激活下一章。

## Phase 1｜工程基础与 Story 创建

**目标：** 建立可运行的模块化单体，并交付 Idea → Concept 纵向切片。

- [x] FastAPI 应用、配置、SQLite、SQLAlchemy、Alembic 和 pytest 基础结构。
- [x] Story、Story Artifact、Generation Task、版本与乐观锁基础模型。
- [x] User Idea 创建、保存、版本读取。
- [x] Story Concept 生成、逐字段编辑、Lock、重新生成和确认。
- [x] Fake Model Adapter 测试与 OpenAI Chat Completions 兼容适配层。

**验收：** 已于 2026-08-10 在 Python 3.13 下执行 `py -3.13 -m alembic upgrade head` 与 `py -3.13 -m pytest -q`；初始迁移成功，4 个 API 测试通过。已覆盖：Idea 不被生成覆盖、Concept 候选不自动应用、确认与 Lock 的追加版本、乐观锁冲突 409、模型失败 502 不改变已保存 Concept。测试运行仅报告 FastAPI/Starlette TestClient 对 httpx 的第三方弃用警告，未影响测试结果。

## Phase 2｜Story Blueprint 与动态状态

**目标：** 交付独立的全局蓝图页面和 Baseline / Living State 双层数据，并定义可供连续写作消费的状态条目契约。

- [x] Characters、World、Initial Timeline、Story Arc 的生成、编辑、Lock 和确认。
- [x] 全局 Entity 唯一性与稳定定义模型。
- [x] Blueprint Baseline 与 Living State 的独立版本及来源记录。
- [x] Blueprint 更新候选、确认和更新历史。
- [x] State Snapshot 三大域：Character State、World State、Timeline State。
- [x] 每条状态保存 subject_id、path、value、source_ref、temporal_scope、certainty、context_policy、updated_at。
- [x] Blueprint 页面提供状态条目来源、时间边界、确认级别和上下文策略展示。
- [x] 从确认 Concept 进入 Blueprint，从确认 Blueprint 进入 Chapter Plan。

**验收：** 已于 2026-08-10 在 Python 3.13 下执行 `py -3.13 -m alembic upgrade head` 与 `py -3.13 -m pytest -q`；Phase 2 迁移成功，10 个 API 回归测试通过。Blueprint 候选任务不会自动确认；`bible` / `arc` 使用 `baseline` 层、`living_state` 强制使用 `living` 层，均为追加版本。只有确认后的 Bible 和 Arc 才可确认 Blueprint 并进入 `blueprint_confirmed`。全局实体按 Story + type + name 唯一，并具备版本和 Lock 保护。状态条目仅接受 `confirmed`，按 Character / World / Timeline 三域独立返回，并保留来源、时间范围、确认级别和上下文策略。根页面已升级为可操作的 Idea → Concept → Blueprint 工作台，所有写入均通过 API；在本机浏览器中已实际完成创建 Story、生成并确认 Concept、生成并确认 Bible / Arc / Living State，最终状态为 `blueprint_confirmed`。新增 `README.md` 提供启动、迁移、测试与手工验收步骤。`/health`、根页面和 README 存在性验证均通过。测试运行仅报告 FastAPI/Starlette TestClient 对 httpx 的第三方弃用警告，未影响结果。

**模型真实接入与验证：** 已接入 Agnes、DeepSeek、Grok 三个 OpenAI Chat Completions 兼容模型，工作台与 API 均可按 provider 选择生成模型。`scripts/verify_models.py` 真实调用三模型各生成一次 Story Concept 全部成功（返回结构完整 JSON）；浏览器界面真实完成一次 Idea → Concept（Grok）→ Blueprint（Agnes）→ `blueprint_confirmed` 闭环，三个 Blueprint 工件均为模型真实生成的中文内容。Grok 不支持 `response_format`，已通过提示词约束与容错 JSON 提取（支持 markdown 代码块包裹）处理；模型调用超时默认 300s 以适配慢速 reasoning 模型。

## Phase 3｜Chapter Plan 与逐章激活

**目标：** 将 Blueprint 拆分为章节卡片，并建立章节访问与计划成熟度规则。

- [x] Chapter Card：标题、目标、summary、主要人物、剧情作用、Arc 关系。
- [x] `plan_status`：第一章为 `fixed`，后序章节为可版本化 `outline`。
- [x] `access_status`：首次仅第一章 `active`，后序全部 `locked`。
- [x] Agent 基于最新 Blueprint / Story State 提出后序 summary 修订。
- [x] 锁定章节不可进入、规划或生成；显示明确解锁条件。

**验收：** 已于 2026-08-11 完成。新增 `chapters` 表及 Story 的 `active_chapter_ordinal`，通过 Alembic 迁移。作者确认 Blueprint 后进入独立 Chapter Plan 页面；Agnes 真实生成 6 张结构化 Chapter Card，Chapter 1 为 `fixed + active`，Chapter 2–6 为 `outline + locked`。浏览器真实验证仅第 1 章可进入 Step 5；锁定章节的服务端 Workspace API 返回 409。后续 outline 可版本化编辑，固定首章不可作为 outline 覆盖。19 项测试通过。

## Phase 4｜Chapter Workspace：章节规划与写作一体化

**目标：** 在唯一的 Chapter Workspace 页面完成 Chapter Context → Events → Scene Plan → Beat Plan，并在同一页继续进入正文生成。

- [ ] 激活章节的 State Snapshot 构建与未来信息过滤。
- [ ] Chapter Events 编辑与 Story Arc 关联。
- [ ] Chapter Events 字段：event_id、ordinal、participants、locations、objective、planned_result、state_impacts、arc_role、status、actual_result_ref。
- [ ] Chapter Events 明确区分 planned_result 与正文后的 actual_result，不把计划直接写入 Story State。
- [ ] Scene Plan：地点、时间、POV、目标、冲突、事件、结果。
- [ ] Beat Plan：顺序、类型、目标、输入上下文和预期变化。
- [ ] 左侧只显示 Chapter → Scene 两级列表；Beat 不进入左侧导航。
- [ ] 右侧依次显示 Chapter 概况、选中 Scene 描述和 Beat 卡片区。
- [ ] Beat banner 支持展开 / 收缩、生成、重新生成；正文区域固定高度并滚动。
- [ ] 默认窄状态栏显示 Snapshot、Delta 和检查摘要；支持覆盖式全局状态面板。

**验收：** Snapshot 只使用前序已确认 Delta；包含 Character / World / Timeline 三大域；每条状态有来源和时间边界；Events 计划与实际结果分离；规划和写作在同一页面；左侧只有两级；Beat 内容不无限拉伸。

## Phase 5｜Chapter Workspace 顺序正文生成与检查点

**目标：** 在 Chapter Workspace 内交付统一顺序生成执行器，不新增独立 Chapter Writing 页面。

- [ ] Beat 级 Markdown 正文版本、应用与单 Beat 重生成。
- [ ] “生成当前 Scene”和“完成本章剩余 Beat”两个入口，均在工作台顶部。
- [ ] 服务端严格校验 Scene / Beat ordinal，禁止跳跃或并行越序生成。
- [ ] Beat 完成：局部 Delta 候选和一致性检查。
- [ ] Scene 完成：Scene Delta、Scene Summary 和后续计划检查。
- [ ] Beat / Scene 检查点生成 proposed 状态候选；只有 Chapter Delta confirmed 后才进入下一章 Snapshot。
- [ ] 失败、取消后从最后已应用 Beat 继续；不丢失正文。

**验收：** 两个生成入口使用同一顺序执行器；未来 Scene 不可点击生成；重生成保留旧版本并使后续临时派生数据失效；状态面板不离开工作台即可展开和收起。

## Phase 6｜Chapter Delta、Blueprint 更新与 Next Chapter

**目标：** 完成一章后形成可审阅的权威状态变化，并进入下一章。

- [ ] Scene Delta 合并为 Chapter Delta；提供证据和冲突结果。
- [ ] 作者编辑、确认或拒绝 Chapter Delta。
- [ ] 确认后更新 Story State 与 Blueprint Living State。
- [ ] Agent 检查后序章节雏形并生成修订候选。
- [ ] 当前章转为 `completed`；仅 ordinal + 1 转为 `active` 并创建 Snapshot。
- [ ] 历史章节变更后的 stale 标记、影响范围和按序重算。

**验收：** Delta 未确认时下一章仍锁定；确认后只激活下一章；计划修订不作为已发生事实；历史恢复创建新版本且不覆盖历史。

## 横向质量门槛

- 所有 schema 变更通过 Alembic；持久化行为覆盖迁移和服务测试。
- API 使用 Pydantic DTO；页面不访问 ORM 或模型服务。
- 生成任务记录参数、上下文引用、输出与状态；日志不记录正文全文、完整提示词或密钥。
- 版本冲突返回 409；任何失败均不得覆盖作者草稿。
- State Snapshot 禁止引用当前章计划结果及未来章节；测试必须验证未来信息不会进入 AI context。
- AI context 仅注入 context_policy=always 或 relevant_only 且在章节时间边界内的 confirmed 状态；proposed 状态必须显式标记。
- Chapter Events 的 planned_result 不得直接合并为 Story State；actual_result 必须引用已应用正文和 Delta。
- UI 覆盖 loading、failed、cancelled、locked、stale、conflict 和 empty 状态。
- 桌面与窄屏均可完成 Idea → 下一章激活的完整闭环。
- Blueprint 的 Characters、World、Initial Timeline、Story Arc 必须使用独立分类容器；禁止跨类混排。
- Blueprint、Chapter Plan、Chapter Planning、Chapter Writing 使用统一流程导航组件。
- Chapter Workspace 左侧必须复用 Chapter → Scene 两级数据和渲染组件；Beat 只在右侧 Beat Card 区域显示。
- Beat Card 必须有固定高度正文容器、滚动、展开/收缩和生成/重生成操作。
- Chapter Workspace 默认显示窄状态栏；全貌状态面板覆盖工作区并复用 Blueprint 的 Characters、World、Timeline、Arc/Living State 分类。

## 当前下一步

1. 为唯一的 Chapter Workspace 添加 State Snapshot、Chapter Events、Scene / Beat 计划模型和同页交互。
2. 将当前 Step 5 入口扩展为设计稿规定的 Chapter → Scene 左栏、Beat Card 内容区与窄状态栏；不新建 Chapter Planning / Writing 页面。
3. 使用真实模型生成当前 active Chapter 的结构化计划，完成来源、时间边界与“计划不等于事实”的回归验证。

## 变更日志

- 2026-08-09：创建技术架构与 UI 设计 HTML 文档。
- 2026-08-09：将文档升级为实现规范，补齐领域状态机、数据、API、异常与 UI 交接规则。
- 2026-08-09：依据产品 Review 重排完整流程；拆分 Concept、Blueprint、Chapter Plan 页面，新增 Blueprint 动态状态、逐章激活、顺序生成和 Beat / Scene / Chapter 检查点计划。
- 2026-08-09：根据原型 Review 修正 Blueprint 分类边界，统一 Story 流程导航，将 Chapter Planning 明确归入 Chapter Plan 阶段，并统一规划/写作页的 Chapter → Scene → Beat 左侧树。
- 2026-08-09：根据工作台 Review 合并规划与写作页面为五步流程中的 Chapter Workspace；左侧收敛为 Chapter → Scene 两级，Beat 改为右侧固定高度可折叠卡片，状态改为窄栏与覆盖式全貌面板。
- 2026-08-10：依据需求 7.1 / 7.2 补充 Blueprint 状态规范：State Snapshot 的 Character / World / Timeline 三域、状态条目来源与时间边界、Chapter Events 计划/实际结果分离，以及连续写作的上下文消费规则。
- 2026-08-10：完成 Phase 1 工程基础与 Idea → Concept 纵向切片：新增 FastAPI/SQLite/Alembic 工程、Story/Artifact/Generation Task 追加版本模型、离线 Fake 与 OpenAI Chat Completions 兼容适配器、Idea/Concept API 及 4 项回归测试；初始迁移与测试在 Python 3.13 下通过。
- 2026-08-10：完成 Phase 2 Story Blueprint 与动态状态：新增 Blueprint 候选生成及显式确认、Baseline / Living State 独立版本约束、全局 Entity 唯一性与 Lock/乐观锁编辑、三域 confirmed 状态条目、`entities` 与 `state_entries` 迁移、Blueprint 状态查看页及 6 项新增 API 回归测试；迁移、10 项测试和页面冒烟验证均在 Python 3.13 下通过。
- 2026-08-10：补齐 Phase 1–2 的可操作 MVP 验收界面与交付文档：根页面升级为 Idea → Concept → Blueprint 工作台，可从浏览器生成、编辑并显式确认候选内容；新增 README 启动、迁移、测试及手工验收说明。浏览器端真实完成一次 `blueprint_confirmed` 闭环，10 项 API 回归测试和 JavaScript 语法检查通过。
- 2026-08-10：修复环境可编辑安装失败：根因为 `pyproject.toml` 缺少 `[build-system]` 声明，导致 `pip install -e .` 构建阶段失败。已补充标准 `setuptools.build_meta` 后端与显式包发现配置；`pip install --dry-run --no-deps -e .` 验证 `build_editable` 构建通过，项目导入与 10 项测试在 Python 3.13 下均正常。
- 2026-08-10：接入三个真实 LLM（Agnes / DeepSeek / Grok）：配置层支持三模型独立 base_url/model/key；模型适配层按 spec 决定是否发送 `response_format`，增加容错 JSON 提取（markdown 包裹/夹杂文字）；生成接口与工作台支持按 provider 选择模型，任务记录所用 provider；新增 `GET /api/v1/models` 列表接口与 5 项模型相关测试。真实调用三模型生成 Concept 全部成功，浏览器界面用真实模型完成 Idea → Concept → Blueprint 全流程回归至 `blueprint_confirmed`；15 项测试全部通过。
- 2026-08-11：重新审查需求、技术架构与 UI 设计，确认此前实现偏向 JSON 后台管理页，未交付文档定义的 Chapter Plan / Chapter Workspace 连续创作体验。重构交付计划：以五步作者流程、结构化作者界面、每 Phase 端到端真实模型与浏览器回归为强制验收；从 Phase 3 起按此标准重建。
- 2026-08-11：完成 Phase 3 的作者体验重构：新增 `planning` 领域、Chapter 聚合与迁移、真实模型 Chapter Plan 生成、独立 Step 4 Chapter Plan 卡片页和受服务端 active 状态保护的 Step 5 入口。Agnes 真实生成 6 章中文计划；浏览器验证首章可进入、后续 5 章锁定；19 项测试通过。当前 Step 5 仅为受保护入口，尚未声称完成 Chapter Context / Scene / Beat / Prose / Delta 功能。
