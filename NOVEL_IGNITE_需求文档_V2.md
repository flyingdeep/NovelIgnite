# NOVEL-IGNITE AI 智能小说生成平台需求文档 V2

## 1. 产品目标

用户输入简短的小说创作意图后，AI Agent 自动完成故事策划、章节规划和正文生成。

支持：
- 短篇小说（单章节）
- 中篇小说
- 长篇小说（多章节，数十万字）

系统需要支持长篇小说的持续生成，并在生成过程中保持人物、世界观、时间线和剧情逻辑的一致性。

核心设计原则：

> Story 是全局事实容器，Chapter 是故事状态的版本节点。

阶段 1～3 用于建立全书基础规划；阶段 3 之后，产品进入以 Chapter 为核心的渐进式生成流程。

---

# 2. 整体流程

```text
User Idea
    ↓
Story Concept
    ↓
Story Blueprint
    ↓
────────────────────
Chapter Workspace
────────────────────
    ↓
Chapter Context
    ↓
Scene Plan
    ↓
Beat Plan
    ↓
Prose Generation
    ↓
State Delta
    ↓
Story State Update
    ↓
Next Chapter
```

---

# 3. 阶段 1：用户创意输入

用户通过单输入框描述小说创作需求。

输入可以是一句话或多句话，可包括：
- 故事主题
- 核心冲突
- 人物设想
- 背景设定
- 写作目的

---

# 4. 阶段 2：Story Concept

AI Agent 根据用户输入生成结构化故事概念。

输出包括：

## 基础信息
- 小说类型
- 写作风格
- 预计长度
- 叙事视角

## 核心内容
- 故事简介
- 核心主题
- 主要冲突
- 故事卖点

用户可以：
- 修改
- 重新生成
- 确认并进入下一阶段

用户确认的关键内容可设置为 Lock。已锁定内容未经用户修改，AI Agent 不得改变。

---

# 5. 阶段 3：Story Blueprint

AI Agent 根据已确认的 Story Concept 创建全书基础规划。

Story Blueprint 包括：

## 5.1 Initial Story Bible

只生成当前规划所需的基础事实，不要求预先穷举整部小说中的所有元素。

包括：

### Characters
- 核心人物
- 基础背景
- 性格
- 职业
- 初始人物关系
- 其他稳定属性

### World
- 基础世界背景
- 地理区域
- 组织和势力
- 世界运行规则

### Initial Timeline
- 故事开始前的重要历史事件
- 故事初始状态

以上内容属于 Story 级全局事实。

---

## 5.2 Story Arc

生成全书主要剧情弧线，包括：
- 核心冲突
- 主要剧情阶段
- 关键转折
- 高潮
- 结局方向
- 主要伏笔和剧情线

---

## 5.3 Chapter Plan

生成全书章节列表及基础规划。

每个 Chapter 包括：
- Chapter ID
- 章节名称
- 章节目标
- 核心事件
- 主要人物
- 剧情推进作用
- 与 Story Arc 的关系

Chapter Plan 是全书的高层规划，不要求在此阶段生成每章全部人物状态、世界状态和详细事件。

用户确认 Chapter Plan 后，进入 Chapter Workspace。

---

# 6. Chapter Workspace

阶段 3 之后，以 Chapter 为主要产品入口。

用户点击任意章节，可以查看和操作该章节对应的完整故事上下文。

每个 Chapter Workspace 包括：

```text
Chapter
├── Chapter Plan
├── State Snapshot
├── Chapter Events
├── Scene Plan
├── Beat Plan
├── Novel Text
└── State Delta
```

---

# 7. Chapter Context

每个 Chapter 在生成前，需要构建该章节专属的 Chapter Context。

包括：

## 7.1 State Snapshot

State Snapshot 表示进入当前章节时，故事世界已经成立的完整有效状态。

主要包括：

### Character State
- 当前地点
- 当前身份
- 当前目标
- 当前掌握的信息
- 当前人物关系
- 身体状态
- 心理状态

### World State
- 当前地点状态
- 组织和势力状态
- 重要物品状态
- 社会或环境变化

### Timeline State
- 已发生的重要事件
- 已解决剧情线
- 未解决剧情线
- 当前有效伏笔

State Snapshot 必须基于当前章节之前已经完成的内容生成，不允许使用未来章节的信息。

---

## 7.2 Chapter Events

描述本章计划发生或推进的重要事件。

每个事件应包含：
- Event ID
- 相关人物
- 相关地点
- 事件目标
- 事件结果
- 对人物或世界状态的影响
- 对 Story Arc 的作用

---

# 8. Scene Plan

每个 Chapter 拆分为多个 Scene。

每个 Scene 包括：
- 场景地点
- 时间
- POV / 视角人物
- 人物目标
- 冲突
- 关键事件
- 场景结果
- 与 Chapter Goal 的关系

Scene 是章节正文生成和局部修改的主要单位。

---

# 9. Beat Plan

每个 Scene 可进一步拆分为多个 Beat。

Beat 用于指导具体正文生成，例如：
- 场景进入
- 人物行动
- 冲突升级
- 信息揭示
- 情绪变化
- 转折
- 悬念设置

AI Agent 实际生成正文时按照 Beat → Scene → Chapter 的顺序执行。

---

# 10. 正文生成

AI Agent 必须按照章节顺序进行正式生成。

同一章节内部按照：

```text
Beat
 ↓
Scene
 ↓
Chapter
```

逐步生成。

生成下一 Scene 时，可使用：
- 当前 Chapter 的 State Snapshot
- Initial Story Bible
- 当前 Chapter Plan
- 已完成 Scene Summary
- 当前章节最近正文
- 当前有效剧情线

不得直接使用未来章节状态作为事实上下文。

---

# 11. State Delta

每个 Scene 或 Chapter 完成后，AI Agent 分析正文中真实发生的变化，生成 State Delta。

State Delta 只记录本次生成产生的状态变化，不重复保存全部 Story State。

包括：

## Character Changes
例如：
- 地点变化
- 身份变化
- 新获得的信息
- 关系变化
- 身体或心理变化

## World Changes
例如：
- 地点被破坏
- 势力关系变化
- 组织状态变化
- 重要物品归属变化

## Timeline Changes
例如：
- 新事件发生
- 剧情线开启
- 剧情线推进
- 剧情线完成
- 新伏笔建立或伏笔回收

State Delta 经一致性检查后写入 Story State。

---

# 12. Story State

Story State 是小说当前时间点的有效故事状态。

逻辑上：

```text
Initial Story State
+
Chapter 1 Delta
+
Chapter 2 Delta
+
...
+
Chapter N Delta
=
Story State @ Chapter N End
```

下一章节的 State Snapshot 基于前一章节完成后的 Story State 创建。

因此：

```text
Chapter N State Snapshot
+
Chapter N State Delta
=
Chapter N+1 State Snapshot
```

系统应支持按任意章节获取当时的 Story State，以支持：
- 历史章节查看
- 章节重写
- 一致性检查
- 防止未来信息污染
- 修改影响分析

---

# 13. 全局实体与章节状态

人物、地点、组织等实体属于 Story，不属于单一 Chapter。

例如：

```text
Character: 林墨
```

只在 Story 层存在一份全局定义。

不同 Chapter 保存的是该人物在不同时间点的状态。

原则：

> Character 属于 Story，Character State 属于 Chapter Context。

同理：

> World Rules 属于 Story，World State 属于 Chapter Context。

> Timeline 属于 Story，Chapter Event 和 Timeline Changes 属于具体 Chapter。

---

# 14. 一致性检查

每个 Scene 或 Chapter 完成后，AI Agent 需要检查：

- 人物行为是否符合当前人物状态
- 人物是否知道不应知道的信息
- 时间线是否冲突
- 世界规则是否被违反
- 已死亡或离场人物是否错误出现
- 物品位置和归属是否冲突
- 人物关系是否前后矛盾
- 剧情线是否出现逻辑断裂

发现冲突时，应在更新 Story State 前处理或提示用户。

---

# 15. 用户调整能力

Phase 1 支持必要的基础调整。

## Story 层
- 修改 Story Concept
- 修改 Initial Story Bible
- 修改 Story Arc
- Lock 关键设定

## Chapter 层
- 修改 Chapter Plan
- 查看当前 State Snapshot
- 修改 Chapter Events
- 调整 Scene Plan
- 调整 Beat Plan
- 重新生成 Scene 或 Chapter

用户修改已经生成的历史章节后，系统需要标记受影响的后续章节，并重新计算对应 Story State。

---

# 16. Phase 2：高级编辑能力

后续支持：
- 人物关系深度调整
- 世界观结构修改
- 大规模剧情调整
- 自动计算修改影响范围
- 自动重构后续章节
- 多版本 Story Branch
- Story State 版本回滚

---

# 17. 核心数据关系

```text
Story
│
├── Story Concept
├── Initial Story Bible
│   ├── Characters
│   ├── Locations
│   ├── Organizations
│   └── World Rules
│
├── Story Arc
│
└── Chapters
    │
    ├── Chapter 1
    │   ├── Chapter Plan
    │   ├── State Snapshot
    │   ├── Chapter Events
    │   ├── Scenes / Beats
    │   ├── Novel Text
    │   └── State Delta
    │
    ├── Chapter 2
    │   ├── Chapter Plan
    │   ├── State Snapshot
    │   ├── Chapter Events
    │   ├── Scenes / Beats
    │   ├── Novel Text
    │   └── State Delta
    │
    └── ...
```

---

# 18. 核心设计原则

1. Story 是全局事实和实体的容器。

2. Chapter 是 Story State 的版本节点，也是阶段 3 之后的主要用户入口。

3. 人物、地点和组织采用全局唯一实体，不在不同章节重复创建。

4. 每个 Chapter 拥有自己的 State Snapshot 和 State Delta。

5. State Snapshot 表示“进入本章时已经成立的事实”。

6. State Delta 表示“本章实际产生的变化”。

7. 下一章节状态由前一章节状态和 Delta 推导产生。

8. AI Agent 只能依据当前时间点有效的信息生成正文，不得使用未来信息。

9. 用户确认并 Lock 的设定具有最高优先级。

10. 长篇小说生成采用“规划 → 生成 → 提取变化 → 更新状态 → 下一章”的循环，而不是一次性线性生成。
