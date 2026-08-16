// 离线演示数据：API 可用时由后端 Blueprint 工件完全覆盖（entries 会被真实数据替换/清空），
// 不进入任何模型输入链；renderBlueprint 在无真实数据时渲染空状态，绝不会展示此处的演示条目。
const blueprintData = {
  characters: {
    title: "人物 · 全局实体",
    description: "人物只在 Story 层定义一次，章节保存的是对应时间点的角色状态。以下字段覆盖背景、动机、关系与创作约束，作为设计与模型生成正文的统一参考。",
    entries: [
      {
        name: "林墨",
        role: "核心主角 · 记忆鉴定师",
        lock: "身份与职业已锁定",
        version: 3,
        updated: "2026-08-10",
        fields: [
          ["身份 / 职业", "旧港区持证记忆鉴定师，负责鉴定、修复与封存私人记忆样本。独立经营一家小型鉴定所，客户多为无力承担正规机构费用的边缘人群。"],
          ["背景故事", "三年前在一次“工作事故”后昏迷，醒来时失去约三年记忆。官方档案记录为设备故障，但事故前夜部分记录缺失，档案页码与系统索引不一致。他保留职业能力，却不记得事故前夜发生了什么。"],
          ["性格特质", "谨慎、克制、观察力强。习惯用专业术语掩盖不安，对“记忆的真实性”近乎偏执。长期受轻度失眠困扰，情绪波动时会出现短暂的机械性重复动作。"],
          ["动机与目标", "表层目标：追查异常样本来源、完成匿名委托。深层目标：找回失去的三年，确认“现在的自己”是否由真实记忆构成。"],
          ["核心关系", "与沈砚为旧识（师出同门，事故后关系疏远）；与乔岚将在 Chapter 02 建立临时合作关系。"],
          ["秘密 / 伏笔", "事故可能并非意外；记忆缺口中可能包含他不愿面对的自我选择。样本编号与他的病历存在关联。"],
          ["能力与限制", "能凭专业经验辨别记忆复制的细节衰减与伪造痕迹；但过度依赖记忆证据，容易被“精心伪造的记忆”误导。"],
          ["创作约束", "不得让林墨提前得知未来章节信息；其“失忆”状态是主线事实，Chapter 08 前任何情节不得使其无损恢复全部记忆。"]
        ],
        history: [
          { version: "v3", date: "2026-08-10", by: "作者确认", note: "补充能力与限制、创作约束", detail: "新增“能力与限制”“创作约束”两个字段，明确失忆状态的不可逆边界；性格特质补充情绪细节。" },
          { version: "v2", date: "2026-08-09", by: "AI 建议", note: "细化动机与关系", detail: "拆分表层/深层目标；补充与沈砚、乔岚的关系描述。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始角色定义", detail: "由 Story Concept 生成的首版角色设定。" }
        ]
      },
      {
        name: "乔岚",
        role: "关键配角 · 地下市场向导",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["身份 / 职业", "地下记忆市场向导，自称“搬运工”，负责为客户引路、找货与规避备案。没有正式执业资格，游离于合法与非法之间。"],
          ["背景故事", "童年时期曾被迫出售家族记忆样本，因此对记忆交易有切身体会。拒绝使用任何记忆复制服务，坚持“记忆只能属于本人”。对旧港地下网络了如指掌。"],
          ["性格特质", "机敏、嘴硬心软。习惯用玩笑话掩盖警惕，对金钱表现出反常的随意。紧张时会无意识地转动右手腕上的旧手环。"],
          ["动机与目标", "表层目标：帮助林墨进入地下拍卖场换取酬劳。深层目标：受某位未知雇主委托，真实目的在 Chapter 06 前必须保持未知。"],
          ["核心关系", "与林墨为雇佣关系，随剧情推进建立信任；与沈砚在地下拍卖事件中存在间接对立。"],
          ["秘密 / 伏笔", "真实雇主是谁、为何对林墨的记忆缺口如此了解，是主要悬念；她的手环可能关联其被出售的家族记忆。"],
          ["能力与限制", "掌握黑市人脉与出入通道，能识别大多数地下记号；但在地下世界的信誉并不完全可靠，可能隐瞒关键信息。"],
          ["创作约束", "Chapter 06 前不得揭示其真实雇主；她提供的每条线索可以包含未知成分，但不能在主角未察觉的情况下主动撒谎。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "作者确认", note: "补充手环与家族记忆伏笔", detail: "新增手环细节作为潜在伏笔；明确真实雇主不得提前揭示。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始角色定义", detail: "由 Story Concept 生成的首版角色设定。" }
        ]
      },
      {
        name: "沈砚",
        role: "关键配角 · 记忆监管局登记员",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["身份 / 职业", "记忆监管局登记员，负责事故档案管理与合法交易备案。拥有中等权限，可调阅大部分档案，但受职位与保密等级限制。"],
          ["背景故事", "与林墨同出鉴定师体系，两人关系曾非常亲近。三年前事故后调任监管局，交接时发现事故档案存在替换痕迹，但未公开追究。"],
          ["性格特质", "谨慎、内疚、原则性强。试图用“按规定办事”掩盖对旧友的愧疚；面对冲突时倾向于回避正面回答。"],
          ["动机与目标", "表层目标：在制度内保护林墨、维持监管局运转。深层目标：掩盖或追查某些监管局内部的违规操作，取决于剧情走向。"],
          ["核心关系", "与林墨旧识但已疏远；与乔岚在地下拍卖事件中间接对立；与监管局内部存在权力博弈。"],
          ["秘密 / 伏笔", "可能掌握事故更多内情；其“调任”可能并非正常人事安排。"],
          ["能力与限制", "能合法调取档案并走正规程序；但受职权范围限制，不能公开对抗监管局，也不能直接进入地下区域。"],
          ["创作约束", "沈砚的立场允许摇摆（保护 vs 规则），但每次动摇都必须有明确证据触发，不能无理由反转。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "作者确认", note: "细化立场摇摆规则", detail: "增加立场约束，规定其动摇必须有证据触发。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始角色定义", detail: "由 Story Concept 生成的首版角色设定。" }
        ]
      }
    ]
  },
  world: {
    title: "世界 · 稳定规则与设定",
    description: "世界规则属于 Baseline，章节中的变化必须经 Delta 确认后才能写入。以下字段为设计与模型提供完整背景参考。",
    entries: [
      {
        name: "旧港区",
        role: "主要地点 · 故事核心舞台",
        lock: "核心设定已锁定",
        version: 2,
        updated: "2026-08-09",
        fields: [
          ["类别", "城市边缘的老工业港口区域。"],
          ["详细描述", "因为排水系统与废弃仓库网络发达，成为地下记忆交易最活跃的区域。白天是普通物流与加工区，入夜后切换为记忆流通的黑市。街道以编号命名，外来者容易迷路。"],
          ["运行规则 / 特点", "非目录内的记忆交易归“地下交易”，不受监管局备案约束；区域监控覆盖率低于市中心，存在大量监控盲区。"],
          ["与故事的关系", "林墨的鉴定所位于旧港区边缘；地下拍卖场藏身于废弃冷冻仓库区；乔岚的活动范围以旧港区为中心。"],
          ["创作约束", "“昼夜切换”与“监控盲区”设定不得被违反；旧港区始终是灰色地带，不能突然变成完全合法的区域。"]
        ],
        history: [
          { version: "v2", date: "2026-08-09", by: "作者确认", note: "补充运行规则与创作约束", detail: "明确地下交易与监控盲区规则，防止生成内容自相矛盾。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始地点定义", detail: "由 Story Concept 生成的首版地点设定。" }
        ]
      },
      {
        name: "记忆监管局",
        role: "组织 / 势力 · 制度性约束",
        lock: "",
        version: 2,
        updated: "2026-08-09",
        fields: [
          ["类别", "官方监管机构。"],
          ["详细描述", "管理记忆商品化的官方机构：发放鉴定师执业资格、备案合法交易、保存事故档案。表面中立，内部存在权限争议与档案管理漏洞，部分人员与地下交易存在暧昧关系。"],
          ["运行规则", "所有合法记忆交易必须备案；事故档案属于最高保密等级，普通登记员无权调阅；鉴定师资格可被吊销。"],
          ["与故事的关系", "沈砚在此任职；档案替换事件指向其内部权限漏洞；林墨的执业资格使其能合法接触样本。"],
          ["伏笔", "监管局内部可能有人与地下拍卖场勾结，是中期反派候选。"]
        ],
        history: [
          { version: "v2", date: "2026-08-09", by: "AI 建议", note: "补充内部漏洞伏笔", detail: "新增内部勾结伏笔，为中期冲突做准备。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始组织定义", detail: "由 Story Concept 生成的首版组织设定。" }
        ]
      },
      {
        name: "记忆复制与衰减规则",
        role: "世界规则 · 不可违背",
        lock: "已锁定，禁止违反",
        version: 3,
        updated: "2026-08-10",
        fields: [
          ["类别", "硬性世界规则。"],
          ["详细描述", "记忆可以复制与转移，但每次复制都会造成细节衰减：颜色失真、情感淡化、时间线模糊。衰减程度取决于复制次数与载体质量。完整的原始记忆只有一份，一旦出售或损坏便不可复原。"],
          ["规则约束", "任何情节都不得让角色无损恢复已衰减的记忆；复制品不能成为“更好的原件”；记忆交易具有不可逆性。"],
          ["与故事的关系", "拍卖的记忆样本因衰减而“残缺”，成为鉴定重点；林墨的专业能力就是识别这种衰减。"],
          ["创作约束", "这是全书最重要的规则锚点。生成 Delta 若与此冲突，必须触发一致性检查并阻止确认。"]
        ],
        history: [
          { version: "v3", date: "2026-08-10", by: "作者确认", note: "明确为一致性检查锚点", detail: "规定与此规则冲突的 Delta 必须被拦截。" },
          { version: "v2", date: "2026-08-09", by: "AI 建议", note: "补充不可逆性描述", detail: "强调原始记忆唯一性，防止后续剧情滥用恢复。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始规则定义", detail: "由 Story Concept 生成的首版世界规则。" }
        ]
      },
      {
        name: "封存样本",
        role: "重要物品 · 主线引子",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["类别", "可携带的重要物品。"],
          ["详细描述", "无名委托人在深夜送来的记忆样本，低温封存，标签被撕去一半，仅剩一个与三年前事故档案匹配的编号前缀。样本未经授权复制，属于“原始记忆”级别，极其珍贵。"],
          ["当前状态", "由林墨暂时保管于鉴定所低温箱（Scene 1 已应用内容，proposed，待 Chapter Delta 确认）。"],
          ["与故事的关系", "样本被证实与林墨本人的事故病历存在关联；其来源决定了匿名委托人的身份。"],
          ["创作约束", "样本的完整性/损坏状态必须与正文严格一致；任何转移保管权都需要 Delta 记录。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "系统提取", note: "更新保管状态", detail: "根据 Scene 1 已应用正文，更新为“由林墨暂时保管”。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始物品定义", detail: "由 Story Concept 生成的首版物品设定。" }
        ]
      }
    ]
  },
  timeline: {
    title: "初始时间线",
    description: "仅收录 Chapter 01 开始前已成立的历史事实。计划事件与未来信息不得进入这个时间边界。",
    entries: [
      {
        name: "记忆商品化",
        role: "12 年前 · 世界级转折",
        lock: "confirmed",
        version: 1,
        updated: "2026-08-08",
        fields: [
          ["时间", "12 年前。"],
          ["详细描述", "记忆提取与复制技术成熟，政府通过《记忆管理法案》将其纳入监管体系。最初的“记忆银行”出现，随后衍生出合法交易与地下交易两个市场。"],
          ["对当前状态的影响", "建立了记忆监管局与鉴定师职业体系；林墨的专业背景由此而来；旧港区成为地下交易中心。"],
          ["相关实体", "记忆监管局、旧港区、记忆复制规则。"]
        ],
        history: [
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始时间线条目", detail: "由 Story Concept 生成的首版历史事件。" }
        ]
      },
      {
        name: "林墨事故失忆",
        role: "3 年前 · 主线起点",
        lock: "confirmed",
        version: 2,
        updated: "2026-08-09",
        fields: [
          ["时间", "3 年前。"],
          ["详细描述", "林墨在旧港鉴定所的一次“工作事故”后昏迷，醒来时失去约三年记忆。官方档案记录为设备故障，但事故前夜部分记录缺失，档案页码与系统索引不一致。"],
          ["对当前状态的影响", "林墨的当前人格建立在“缺失三年”之上；这是故事核心冲突的起点，也是样本编号关联的基础。"],
          ["相关实体", "林墨、沈砚、记忆监管局、封存样本。"]
        ],
        history: [
          { version: "v2", date: "2026-08-09", by: "作者确认", note: "补充档案异常细节", detail: "加入页码与索引不一致的异常，为 Chapter 01 的档案检查作铺垫。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始时间线条目", detail: "由 Story Concept 生成的首版历史事件。" }
        ]
      },
      {
        name: "匿名委托送达",
        role: "本章开始前 · 触发主线",
        lock: "",
        version: 1,
        updated: "2026-08-10",
        fields: [
          ["时间", "Chapter 01 开始前（当前）。"],
          ["详细描述", "一名未署名的委托人深夜送来异常样本，要求林墨在限定时间内完成鉴定，且不得上报监管局。"],
          ["对当前状态的影响", "触发 Chapter 01 主线；林墨因此开始追查样本来源。"],
          ["相关实体", "林墨、封存样本、旧港鉴定所。"]
        ],
        history: [
          { version: "v1", date: "2026-08-10", by: "系统提取", note: "Scene 1 已应用后登记", detail: "根据已应用正文提取为 confirmed 事实。" }
        ]
      }
    ]
  },
  arc: {
    title: "故事弧 · 身份谜题",
    description: "故事弧记录全书方向、阶段与伏笔。planned 内容不是已发生事实，需随正文确认逐步落地。",
    entries: [
      {
        name: "第一幕 · 建立",
        role: "Chapter 01-03",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["目的", "建立“身份谜题”主线，让林墨发现记忆缺口并非自然形成，并决定深入调查。"],
          ["关键事件", "匿名委托 → 档案替换被发现 → 收到地下拍卖邀请函 → 潜入拍卖会 → 发现与自己相关的记忆样本。"],
          ["核心冲突与转折", "林墨从“被动的受害者”转变为“主动的追查者”；首次反转：样本与自身病历存在直接关联。"],
          ["伏笔铺设", "样本编号、沈砚的回避、监管局档案漏洞、乔岚的真实雇主。"],
          ["当前状态", "进行中 · Chapter 01-03 planned（Chapter 01 正在生成）。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "作者确认", note: "明确第一幕边界", detail: "确认 Chapter 01-03 归属第一幕，并记录关键事件顺序。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始故事弧定义", detail: "由 Story Concept 生成的首版故事弧。" }
        ]
      },
      {
        name: "第二幕 · 推进与反转",
        role: "Chapter 04-08",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["目的", "把核心问题从“记忆被谁出售”推向“记忆是否由自己出售”，同时制造信任危机。"],
          ["关键事件", "监管者警告 → 衰减记忆中的事故前夜碎片 → 乔岚双重委托冲突 → 记忆样本与自我重叠。"],
          ["核心冲突与转折", "找回真相与保护现状的正面冲突；林墨与乔岚、沈砚之间的信任危机；核心反转点预留于此。"],
          ["伏笔铺设", "事故前夜的“某个决定”、监管局内部权限、拍卖场的真实组织。"],
          ["当前状态", "待生成 · 依据前序章节演化（当前为雏形计划）。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "AI 建议", note: "补充信任危机线索", detail: "细化冲突维度，加入乔岚双重委托悬念。" },
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始故事弧定义", detail: "由 Story Concept 生成的首版故事弧。" }
        ]
      },
      {
        name: "第三幕 · 反转与结局",
        role: "Chapter 09-12",
        lock: "",
        version: 1,
        updated: "2026-08-08",
        fields: [
          ["目的", "完成身份谜题闭环，回答“记忆是否定义自我”这一核心主题。"],
          ["关键事件", "记忆部分复原 → 直面事故真相 → 在地下拍卖场做出最终选择。"],
          ["核心冲突与转折", "自由与真相的代价；结局方向：主题落地，拒绝廉价和解。"],
          ["伏笔回收", "样本来源、乔岚雇主、沈砚立场、事故前夜的决定。"],
          ["当前状态", "待生成 · 结局方向已规划，允许作者在写作过程中修订。"]
        ],
        history: [
          { version: "v1", date: "2026-08-08", by: "AI 生成", note: "初始故事弧定义", detail: "由 Story Concept 生成的首版结局方向。" }
        ]
      }
    ]
  },
  living: {
    title: "Living State · 当前有效投影",
    description: "只由已确认 Chapter Delta 更新。此视图与 Chapter Workspace 的状态面板使用同一分类，作为下一章 Snapshot 的事实来源。",
    entries: [
      {
        name: "角色状态",
        role: "当前快照 · confirmed",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["林墨", "位于旧港鉴定所；身份为记忆鉴定师；已接到匿名委托；尚未进入地下市场。"],
          ["乔岚", "尚未出场；与林墨尚无已确认关系。"],
          ["沈砚", "尚未直接出场；监管局职务状态正常。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "系统提取", note: "Scene 1 应用后更新", detail: "登记匿名委托与样本保管状态。" },
          { version: "v1", date: "2026-08-09", by: "系统初始化", note: "初始状态投影", detail: "由 Initial Story State 初始化。" }
        ]
      },
      {
        name: "世界状态",
        role: "当前快照 · confirmed / proposed",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["旧港鉴定所", "可正常使用；封存样本低温箱在林墨控制下（proposed）。"],
          ["记忆监管局", "保持中立；档案替换线索尚未公开。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "系统提取", note: "Scene 1 应用后更新", detail: "更新样本保管归属。" },
          { version: "v1", date: "2026-08-09", by: "系统初始化", note: "初始状态投影", detail: "由 Initial Story State 初始化。" }
        ]
      },
      {
        name: "时间线状态",
        role: "当前快照 · confirmed",
        lock: "",
        version: 2,
        updated: "2026-08-10",
        fields: [
          ["已发生", "匿名委托送达；林墨开始检查事故档案。"],
          ["未解决剧情线", "事故真相、样本来源、身份谜题。"],
          ["有效伏笔", "样本编号与林墨记忆缺口相关；沈砚的回避。"]
        ],
        history: [
          { version: "v2", date: "2026-08-10", by: "系统提取", note: "Scene 1 应用后更新", detail: "新增已发生事件与有效伏笔。" },
          { version: "v1", date: "2026-08-09", by: "系统初始化", note: "初始状态投影", detail: "由 Initial Story State 初始化。" }
        ]
      }
    ]
  }
};

const books = [
  { id: "b1", title: "记忆拍卖场", subtitle: "科幻 · 悬疑 · 中篇", status: "inprogress", progress: "第 2 章 / 12 章", cover: ["#4d8dff", "#14243f"], updated: "2 小时前", stage: "writing", idea: "在记忆可以交易的近未来，一位失忆的鉴定师发现自己的过去正被分批拍卖。他必须潜入地下记忆市场，在找回真相与保护现在的自我之间做出选择。" },
  { id: "b2", title: "雾中灯塔", subtitle: "情感 · 成长 · 短篇", status: "completed", progress: "已完成 · 8 章", cover: ["#50d6a1", "#0f352b"], updated: "3 天前", stage: "done", idea: "守塔人独自守护着海湾的灯塔，直到某天灯塔发出了一封写给多年后自己的信。" },
  { id: "b3", title: "废墟图书馆", subtitle: "奇幻 · 冒险 · 长篇", status: "inprogress", progress: "第 7 章 / 40 章", cover: ["#ac84ff", "#2b1d4d"], updated: "昨天", stage: "writing", idea: "世界的图书馆沉入废墟，最后一位图书管理员必须修复知识的种子。" },
  { id: "b4", title: "第七档案室", subtitle: "悬疑 · 惊悚 · 中篇", status: "inprogress", progress: "第 1 章 / 15 章", cover: ["#f2bc61", "#3d2c13"], updated: "刚刚", stage: "writing", idea: "编号第七的档案室里，每一份档案都封印着一段被删除的现实。" }
];

const chapters = [
  ["01", "消失的委托人", "接受委托，发现三年记忆存在人为缺口。", "active"],
  ["02", "拍卖目录", "潜入地下拍卖，发现标记为自己的记忆样本。", "locked"],
  ["03", "记忆样本", "验证样本，揭示记忆曾被主动出售。", "locked"],
  ["04", "监管者来信", "监管局旧识要求林墨停止调查。", "locked"],
  ["05", "损坏的证词", "从衰减记忆中拼合事故前夜的片段。", "locked"],
  ["06", "双重委托", "乔岚的真实雇主与林墨产生冲突。", "locked"]
];

const scenes = [
  { id: 1, name: "深夜委托", hint: "已完成 · 3 个 Beat", status: "done" },
  { id: 2, name: "缺失报告", hint: "当前 · 3 个 Beat", status: "current" },
  { id: 3, name: "邀请函", hint: "计划中 · 等待前序", status: "planned" },
  { id: 4, name: "雨中离场", hint: "雏形 · 尚未可用", status: "locked" }
];

const sceneContent = {
  1: {
    title: "Scene 1 · 深夜委托",
    subtitle: "地点：旧港鉴定所 · 时间：深夜 · POV：林墨",
    overview: "场景目标：让林墨接触异常样本；结果：他发现样本编号与自己的事故病历存在关联。",
    beats: [
      ["Beat 1 · 后门的脚步", "已完成", "林墨结束加班时，发现后门门缝下多了一张没有署名的纸条。", "done"],
      ["Beat 2 · 封存样本", "已完成", "低温箱内的样本没有来源签名，却带着三年前事故档案的编号前缀。", "done"],
      ["Beat 3 · 匿名委托", "已完成", "委托人要求他在天亮前鉴定样本，且不要通知监管局。", "done"]
    ]
  },
  2: {
    title: "Scene 2 · 缺失报告",
    subtitle: "地点：旧港鉴定所 · 时间：凌晨 · POV：林墨",
    overview: "场景目标：寻找事故档案；冲突：系统归档的报告页码被人为替换。生成不能提前揭示幕后身份。",
    beats: [
      ["Beat 1 · 返回档案室", "已完成", "林墨打开档案室，发现纸质原件与系统索引在同一个页码处出现了不同的编号。", "done"],
      ["Beat 2 · 检查事故档案", "当前 Beat", "生成目标：林墨确认记录被人为替换，但只能获得操作痕迹，不能提前知道替换者身份。", "current"],
      ["Beat 3 · 病历签名", "等待前序 Beat", "待 Beat 2 应用后生成。签名应把线索指向下一场景，不直接结案。", "planned"]
    ]
  },
  3: {
    title: "Scene 3 · 邀请函",
    subtitle: "地点：旧港鉴定所 · 时间：清晨前 · POV：林墨",
    overview: "计划：匿名人留下地下拍卖邀请函；该计划仍不是已发生事实。",
    beats: [["Beat 1 · 未解锁", "等待前序 Scene", "必须完成 Scene 2，才能使用前序正文和临时上下文生成。", "planned"]]
  },
  4: {
    title: "Scene 4 · 雨中离场",
    subtitle: "章节雏形",
    overview: "这个场景尚不进入当前生成上下文。",
    beats: [["Beat 1 · 尚未可用", "已锁定", "完成前序 Scene 后，根据最新状态和计划演化。", "planned"]]
  }
};

let activeScene = 2;
let activeBook = null;
let pendingDeleteId = null;
let generatedBeat = false;
let toastTimer;
let aiConfig = { model: "DeepSeek V4 Flash", temperature: 0.7, reasoning: "medium", version: 1 };
let blueprintHasData = false;
// 模型可用性探测结果（[{provider,name,model,available,reason,latency_ms}]）；null = 尚未探测
let modelAvailability = null;
// Phase 5 workspace state: real API context when available
let currentWorkspaceContext = null;
let currentActiveChapterId = null;
// Phase 6+ reader state: full-novel reading mode (step 6)
let readerData = null;
let readerActiveChapter = null;
let readerActiveScene = null;
// 阶段 → 可访问屏幕映射（与后端 Story.stage 对应；未推进到的步骤禁止进入）。
const STAGE_SCREENS = {
  idea: ["idea"],
  idea_locked: ["idea", "concept"],
  concept_confirmed: ["idea", "concept", "blueprint"],
  blueprint_review: ["idea", "concept", "blueprint"],
  blueprint_confirmed: ["idea", "concept", "blueprint", "chapters"],
  chapter_planning: ["idea", "concept", "blueprint", "chapters", "workspace"],
  writing: ["idea", "concept", "blueprint", "chapters", "workspace", "read", "cover", "book"],
  done: ["idea", "concept", "blueprint", "chapters", "workspace", "read", "cover", "book"],
};
const SCREEN_LOCK_HINTS = {
  concept: "该步骤尚未解锁：请先在「创意」页生成概念。",
  blueprint: "该步骤尚未解锁：请先确认概念，蓝图才会解锁。",
  chapters: "该步骤尚未解锁：请先确认蓝图，章节规划才会解锁。",
  workspace: "该步骤尚未解锁：请先生成章节计划，工作台才会解锁。",
  read: "该步骤尚未解锁：请按章节顺序推进写作，阅读模式在全书完成后解锁。",
  cover: "该步骤尚未解锁：封面与插画在阅读模式生成后才能使用（可跳过）。",
  book: "该步骤尚未解锁：实体书模式在阅读模式生成后才能使用。",
};
const API_BASE = "/api/v1";
let apiAvailable = false;

function canAccessScreen(screen) {
  if (screen === "works" || screen === "models") return true;
  const book = currentBook();
  if (!book) return false;
  return (STAGE_SCREENS[book.stage] || []).includes(screen);
}

function lockHintFor(screen) {
  return SCREEN_LOCK_HINTS[screen] || "该步骤尚未解锁，请先完成前面的步骤。";
}

function updateStepbarLock() {
  const book = currentBook();
  document.querySelectorAll("[data-nav]").forEach((button) => {
    const nav = button.dataset.nav;
    if (nav === "works" || nav === "models") {
      button.classList.remove("disabled");
      button.setAttribute("aria-disabled", "false");
      return;
    }
    const locked = !book || !(STAGE_SCREENS[book.stage] || []).includes(nav);
    button.classList.toggle("disabled", locked);
    button.setAttribute("aria-disabled", String(locked));
  });
}

async function refreshBookStage(book) {
  if (!apiAvailable || !book) return;
  try {
    const work = await apiRequest(`/works/${book.id}`);
    book.stage = work.stage;
    book.version = work.version;
    book.status = work.stage === "done" ? "completed" : "inprogress";
    updateStepbarLock();
  } catch (error) { /* keep current stage */ }
}

async function apiRequest(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs || 160000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, signal: controller.signal, ...options });
  } catch (error) {
    if (error && error.name === "AbortError") throw new Error("请求超时");
    throw error;
  } finally {
    clearTimeout(timer);
  }
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = (body && typeof body.detail === "string" ? body.detail : "") || "";
    } catch (error) { /* 非 JSON 错误体 */ }
    // 服务端模型链路不可达/繁忙：给出一致、明确的提示（供生成 catch 展示）
    if (response.status === 502 || response.status === 503 || response.status === 504 || response.status === 429) {
      const err = new Error(detail || "模型服务暂时不可达或繁忙，请稍后重试，或换个模型。");
      err.status = response.status;
      throw err;
    }
    const err = new Error(detail || `API ${response.status}`);
    err.status = response.status;
    throw err;
  }
  return response.status === 204 ? null : response.json();
}

// 生成失败提示：优先显示模型服务不可达/繁忙等明确原因，否则回退通用文案
function generationFailToast(error, fallback) {
  const msg = error && error.message;
  if (msg && /模型|服务|超时|繁忙/.test(msg)) toast(msg);
  else toast(fallback);
}

function apiWorkToBook(work) {
  return {
    id: work.id,
    title: work.title,
    subtitle: work.stage === "idea" ? "尚未分类 · 待生成" : "创作中 · 进行中",
    status: work.stage === "done" ? "completed" : "inprogress",
    progress: work.progress_text,
    cover: [work.cover_color || "#3f6db5", "#141f33"],
    updated: work.updated_at ? new Date(work.updated_at).toLocaleString("zh-CN") : "刚刚",
    stage: work.stage,
    idea: work.idea_text || "",
    version: work.version || 1
  };
}

async function loadWorksFromApi() {
  try {
    const works = await apiRequest("/works");
    books.splice(0, books.length, ...works.map(apiWorkToBook));
    apiAvailable = true;
  } catch (error) {
    apiAvailable = false;
  }
}

function conceptPayloadFromForm() {
  const selling = [...document.querySelectorAll("#concept-selling-points li")].map((item) => item.textContent.trim()).filter(Boolean);
  return {
    genre: document.querySelector("#concept-genre")?.value || "",
    viewpoint: document.querySelector("#concept-viewpoint")?.value || "",
    style: document.querySelector("#concept-style")?.value || "",
    length: document.querySelector("#concept-length")?.value || "",
    summary: document.querySelector("#concept-summary")?.value || "",
    theme: document.querySelector("#concept-theme")?.textContent.trim() || "",
    conflict: "",
    selling_points: selling,
  };
}

function applyConceptPayload(payload) {
  const setValue = (selector, value) => { const element = document.querySelector(selector); if (element && value !== undefined) element.value = value; };
  setValue("#concept-genre", payload.genre);
  setValue("#concept-viewpoint", payload.viewpoint);
  setValue("#concept-style", payload.style);
  setValue("#concept-length", payload.length);
  setValue("#concept-summary", payload.summary);
  const theme = document.querySelector("#concept-theme");
  if (theme && payload.theme !== undefined) theme.textContent = payload.theme;
  const list = document.querySelector("#concept-selling-points");
  if (list) {
    const items = Array.isArray(payload.selling_points)
      ? payload.selling_points.map((item) => String(item).trim()).filter(Boolean)
      : typeof payload.selling_points === "string"
        ? payload.selling_points.split(/[；;\n]/).map((item) => item.trim()).filter(Boolean)
        : [];
    list.innerHTML = items.length ? items.map((item) => `<li>${item}</li>`).join("") : `<li class="placeholder">（等待 AI 生成卖点）</li>`;
  }
}

async function loadConceptForCurrentStory() {
  const book = currentBook();
  if (!apiAvailable || !book) return;
  try {
    const artifact = await apiRequest(`/stories/${book.id}/concept`);
    applyConceptPayload(artifact.payload);
    window.currentConceptVersion = artifact.version;
    window.currentConceptStatus = artifact.status;
    const version = document.querySelector("#concept-version");
    if (version) version.textContent = `AI 候选 · v${artifact.version}`;
    document.querySelector("#concept-stage-note").textContent = artifact.status === "confirmed" ? "已确认 · 当前版本为权威 Concept" : "AI 候选 · 尚未确认";
    const confirm = document.querySelector("#confirm-concept");
    if (confirm) confirm.style.display = artifact.status === "confirmed" ? "none" : "";
  } catch (error) {
    window.currentConceptVersion = 0;
  }
}

const BLUEPRINT_FIELD_KEYWORDS = ["性格特质", "性格", "职业身份", "职业", "身份", "动机", "目标", "缺陷", "欲望与软肋", "软肋", "欲望", "初始关系", "核心关系", "关系", "背景故事", "背景", "秘密与伏笔", "秘密", "伏笔", "能力与限制", "能力", "创作约束", "约束", "外貌", "形象", "关键事件", "结局", "规则", "设定"];

// 后端或模型可能把 fields 输出成对象 / 二维数组 / 字符串；统一归一化为 [label, value] 列表，
// 避免 Object.entries(字符串) 把字段逐字拆散成「0性 1格 2冷…」矩阵。
function normalizeUiFields(fields) {
  // 格式化字段值：数组/对象数组（如 living timeline 的 events）也要转成可读文本，
  // 否则直接 join 会输出一长串 [object Object]。
  const fmt = (v) => {
    if (Array.isArray(v)) {
      return v.map((x) => (typeof x === "object" && x !== null ? Object.entries(x).map(([k, val]) => `${k}：${val}`).join("，") : String(x))).join("；");
    }
    if (v && typeof v === "object") {
      return Object.entries(v).map(([k, val]) => `${k}：${val}`).join("；");
    }
    return String(v == null ? "" : v);
  };
  if (Array.isArray(fields)) {
    return fields.map((f) => {
      if (Array.isArray(f) && f.length >= 2) return [fmt(f[0]), fmt(f[1])];
      return ["设定", fmt(f)];
    });
  }
  if (typeof fields === "string") {
    const segments = fields.split(/[；;。\n]/).map((s) => s.trim()).filter(Boolean);
    if (!segments.length) return [["设定", fields]];
    const out = [];
    let counter = 1;
    for (const seg of segments) {
      let label = null, value = seg;
      const m = seg.match(/^(.{1,8}?)[为是:：](.+)$/);
      if (m && m[2].trim()) { label = m[1].trim(); value = m[2].trim(); }
      if (label === null) {
        const matched = BLUEPRINT_FIELD_KEYWORDS.find((k) => seg.startsWith(k));
        if (matched) { label = matched; value = seg.slice(matched.length).replace(/^[为是:：、，\s]+/, ""); }
        else { label = "设定" + counter++; }
      }
      if (out.some(([l]) => l === label)) label = label + counter++;
      out.push([label, value]);
    }
    return out;
  }
  if (fields && typeof fields === "object") {
    return Object.entries(fields).map(([label, value]) => [label, fmt(value)]);
  }
  return [["设定", fmt(fields)]];
}

function blueprintPayloadToUi(kind, artifact) {
  if (!blueprintData[kind]) return;
  const entries = artifact?.payload && Array.isArray(artifact.payload.entries) ? artifact.payload.entries : [];
  blueprintData[kind].entries = entries.map((entry) => {
    return {
      name: entry.name || kind,
      role: entry.role || "全局设定",
      version: artifact.version,
      updated: artifact.updated_at?.slice(0, 10) || "刚刚",
      lock: artifact.locked_paths?.length ? "部分字段已锁定" : "",
      fields: normalizeUiFields(entry.fields),
      history: [{ version: `v${artifact.version}`, date: artifact.updated_at?.slice(0, 10) || "刚刚", by: artifact.status === "confirmed" ? "作者确认" : "AI 候选", note: "来自真实 Blueprint API", detail: "当前版本从后端 Story Artifact 读取。" }],
    };
  });
}

function livingPayloadToUi(artifact) {
  // Render Living State from the real living_state artifact (domains projection), never demo data.
  const payload = artifact?.payload || {};
  const domains = payload.domains || {};
  const confirmed = payload.certainty || "confirmed";
  const domainMeta = [
    ["characters", "角色状态", `当前快照 · ${confirmed}`],
    ["world", "世界状态", "当前快照 · confirmed / proposed"],
    ["timeline", "时间线状态", "当前快照 · confirmed"],
  ];
  const entries = [];
  for (const [key, title, role] of domainMeta) {
    const state = domains[key]?.state || {};
    const list = Array.isArray(state.entries) ? state.entries : [];
    const fields = list.map((entry) => {
      const lines = normalizeUiFields(entry.fields).map(([k, v]) => `${k}：${v}`);
      return [entry.name || key, lines.join("；") || "（无明细）"];
    });
    entries.push({
      name: title,
      role,
      lock: "",
      version: artifact.version,
      updated: artifact.updated_at?.slice(0, 10) || "刚刚",
      fields,
      history: [{ version: `v${artifact.version}`, date: artifact.updated_at?.slice(0, 10) || "刚刚", by: "系统投影", note: "来自真实 Living State", detail: `当前 Living State v${artifact.version}，由已确认 Chapter Delta 更新。` }],
    });
  }
  blueprintData.living.entries = entries;
  blueprintData.living.version = artifact.version || 1;
}

async function loadBlueprintForCurrentStory() {
  const book = currentBook();
  if (!apiAvailable || !book) return;
  try {
    let data = await apiRequest(`/stories/${book.id}/blueprint`);
    let hasAny = ["characters", "world", "timeline", "arc"].some((kind) => data[kind]);
    // 自愈：概念已确认但蓝图缺失（确认后自动生成中断/失败）时，进入蓝图页自动补齐。
    if (!hasAny && (book.stage === "concept_confirmed" || book.stage === "blueprint_review")) {
      showThinking("正在自动生成蓝图候选…", "检测到概念已确认但蓝图缺失，自动补齐 Characters / World / Timeline / Arc");
      try {
        const result = await apiRequest(`/stories/${book.id}/blueprint/generations`, { method: "POST", body: JSON.stringify({ action: "generate_blueprint" }), timeoutMs: 300000 });
        result.artifacts.forEach((artifact) => { if (blueprintData[artifact.kind]) blueprintPayloadToUi(artifact.kind, artifact); });
        blueprintHasData = true;
        window.currentBlueprintVersions = Object.fromEntries(result.artifacts.map((artifact) => [artifact.kind, artifact.version]));
        toast("蓝图候选已自动生成，请查看后确认。");
        data = await apiRequest(`/stories/${book.id}/blueprint`);
        hasAny = true;
      } catch (e) {
        blueprintHasData = false;
        window.currentBlueprintVersions = {};
        toast("蓝图自动生成失败，可点击「生成候选」重试。");
        renderBlueprintEmpty();
        return;
      } finally {
        hideThinking();
      }
    }
    window.currentBlueprintVersions = window.currentBlueprintVersions || {};
    if (hasAny) {
      // 关键：从 API 加载到已有蓝图时必须置位，否则 renderBlueprint 会渲染空状态
      blueprintHasData = true;
      Object.entries(data).forEach(([kind, artifact]) => { if (artifact && blueprintData[kind]) blueprintPayloadToUi(kind, artifact); });
      ["characters", "world", "timeline", "arc"].forEach((kind) => { if (data[kind]) window.currentBlueprintVersions[kind] = data[kind].version; });
    } else {
      blueprintHasData = false;
    }
    const living = data.living_state;
    if (living && living.payload && living.payload.domains) {
      livingPayloadToUi(living);
    }
    const confirmed = ["characters", "world", "timeline", "arc"].every((kind) => data[kind]?.status === "confirmed");
    document.querySelector("#confirm-blueprint").style.display = confirmed ? "none" : "";
    const toChapters = document.querySelector("#to-chapters");
    if (toChapters) toChapters.style.display = confirmed ? "" : "none";
    document.querySelector("#blueprint-stage-note").textContent = confirmed ? "已确认 · 当前版本为权威 Blueprint" : (hasAny ? "AI 候选 · 尚未确认" : "尚未生成");
    // 蓝图更新建议（场景/章节完成后的独立 review 环节产出，待作者确认）
    try {
      const reviews = await apiRequest(`/stories/${book.id}/blueprint-reviews`, { timeoutMs: 10000 });
      renderBlueprintReviews(reviews);
    } catch (error) {
      renderBlueprintReviews([]);
    }
    renderBlueprint(document.querySelector(".blueprint-tab.active")?.dataset.blueprint || "characters");
  } catch (error) {
    window.currentBlueprintVersions = {};
  }
}

function renderBlueprintReviews(reviews) {
  // 蓝图更新活动已自动应用到各分类（append-only 新版本 + 履历），此处只作轻量摘要提示，
  // 不再是「待确认」长列表；点击各分类「查看更新履历」可看每次变更。
  const applied = (reviews || []).filter((r) => r.status === "applied");
  const total = applied.reduce((n, r) => n + (r.suggestions || []).length, 0);
  let el = document.querySelector("#blueprint-reviews-banner");
  if (!total) {
    if (el) el.remove();
    return;
  }
  if (!el) {
    el = document.createElement("div");
    el.id = "blueprint-reviews-banner";
    // 插入到 .blueprint-layout 同级之前；不能放进 grid，否则会抢占一列并挤窄蓝图内容。
    const layout = document.querySelector(".blueprint-layout");
    if (layout && layout.parentElement) {
      layout.parentElement.insertBefore(el, layout);
    }
  }
  const latest = applied[applied.length - 1];
  const recent = (latest && latest.suggestions || []).slice(0, 3).map((s) => {
    const act = s.action === "add" ? "新增" : "修改";
    const kindLabel = { characters: "人物", world: "世界", timeline: "时间线", arc: "剧情弧" }[s.kind] || s.kind;
    return `<li><b>${act}·${kindLabel}</b>「${s.target || ""}」：${s.change || ""}</li>`;
  }).join("");
  el.innerHTML = `<div style="margin:12px 0;padding:10px 12px;border:1px solid #3fae6a;border-radius:10px;background:rgba(63,174,106,.08)"><b style="color:#3fae6a">✓ 蓝图更新已自动应用（累计 ${total} 条）</b><p style="margin:4px 0 0;font-size:12px;color:#9aa4b5">场景/章节完成后的 review 已自动更新对应分类设定（新版本保留、锁定字段不覆盖），可在各分类「查看更新履历」中追溯。</p>${recent ? `<ul style="margin:8px 0 0;padding-left:18px;font-size:13px;line-height:1.7">${recent}</ul>` : ""}</div>`;
}

async function saveConceptCandidate() {
  const book = currentBook();
  if (!apiAvailable || !book || !window.currentConceptVersion) return;
  const response = await apiRequest(`/stories/${book.id}/concept`, {
    method: "PUT",
    body: JSON.stringify({ payload: conceptPayloadFromForm(), locked_paths: [], expected_version: window.currentConceptVersion }),
  });
  window.currentConceptVersion = response.version;
  applyConceptPayload(response.payload);
}

function toast(message) {
  const el = document.querySelector("#toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
}

function showScreen(id) {
  if (id !== "works" && !canAccessScreen(id)) {
    toast(lockHintFor(id));
    return;
  }
  document.querySelectorAll(".screen").forEach((screen) => screen.classList.toggle("active", screen.id === id));
  document.querySelectorAll("[data-nav]").forEach((button) => button.classList.toggle("active", button.dataset.nav === id));
  if (id === "workspace") loadWorkspaceContext();
  if (id === "works") renderBooks();
  if (id === "idea") renderIdea();
  if (id === "concept") loadConceptForCurrentStory();
  if (id === "blueprint") loadBlueprintForCurrentStory();
  if (id === "chapters") loadChaptersForCurrentStory();
  if (id === "read") loadReaderForCurrentStory();
  if (id === "cover") loadCoverForCurrentStory();
  if (id === "book") loadBookForCurrentStory();
  updateTopState();
  updateStepbarLock();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderBlueprintEmpty() {
  document.querySelector("#blueprint-content").innerHTML = `
    <section class="content-panel panel">
      <div class="content-head"><div><h2>故事蓝图</h2><p>该作品尚未生成蓝图。不同概念会得到完全不同的四类全局设定。</p></div></div>
      <div class="books-empty"><h3>尚未生成蓝图</h3><p>请确认 Concept 后，点击右上角「生成候选」，AI 将根据当前概念生成 Characters / World / Timeline / Arc。</p></div>
    </section>`;
}

function renderBlueprint(kind = "characters") {
  document.querySelectorAll(".blueprint-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.blueprint === kind));
  // 无真实数据（含未打开作品）时只渲染空状态，绝不展示顶层演示条目。
  if (!blueprintHasData) {
    renderBlueprintEmpty();
    return;
  }
  const entry = blueprintData[kind];
  const entries = entry.entries || [];
  const cards = entries.length
    ? entries.map((item, index) => `
    <article class="bp-entry">
      <div class="bp-entry-head">
        <div><h3>${item.name}</h3><span class="bp-role">${item.role}</span></div>
        <div class="bp-entry-tags">${item.lock ? `<span class="tag amber">🔒 ${item.lock}</span>` : ""}<span class="tag blue">v${item.version} · 更新于 ${item.updated}</span></div>
      </div>
      <div class="bp-fields">${item.fields.map(([label, value]) => `<div class="bp-field"><span>${label}</span><p>${value}</p></div>`).join("")}</div>
      <div class="bp-entry-foot"><button class="text-button history-link" type="button" data-history="${kind}|${index}">查看更新履历（${item.history.length} 条）</button></div>
    </article>`).join("")
    : `<div class="books-empty"><h3>该分类暂无条目</h3><p>重新生成候选后，AI 会为该分类填充完整设定。</p></div>`;
  document.querySelector("#blueprint-content").innerHTML = `
    <section class="content-panel panel">
      <div class="content-head"><div><h2>${entry.title}</h2><p>${entry.description}</p></div><button class="secondary-button" type="button" data-toast="此处展示的是可编辑的原型结构；锁定字段需要作者显式解除后才能修改。">编辑设定</button></div>
      <div class="bp-entries">${cards}</div>
      <div class="living-banner"><b>状态更新边界：</b> Beat / Scene 只生成 proposed 候选；仅 Chapter Delta 经作者确认后更新 Living State，并作为下一章 Snapshot 的新增事实。</div>
    </section>`;
  document.querySelectorAll(".blueprint-tab").forEach((tab) => {
    const k = tab.dataset.blueprint;
    if (k && k !== "living" && blueprintData[k]) {
      const count = tab.querySelector("span");
      if (count) count.textContent = String((blueprintData[k].entries || []).length);
    }
  });
  document.querySelectorAll(".blueprint-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.blueprint === kind));
}

function currentBook() {
  return books.find((book) => book.id === activeBook) || null;
}

async function refreshStoryTitle(book) {
  try {
    const work = await apiRequest(`/works/${book.id}`);
    const oldTitle = book.title;
    book.title = work.title;
    book.version = work.version;
    book.updated = work.updated_at ? new Date(work.updated_at).toLocaleString("zh-CN") : book.updated;
    updateTopState();
    return book.title !== oldTitle;
  } catch (error) {
    return false;
  }
}

function openTitleModal() {
  const book = currentBook();
  if (!book) return;
  document.querySelector("#title-input").value = book.title;
  showModal("#title-modal");
  document.querySelector("#title-input").focus();
}

async function saveTitle() {
  const book = currentBook();
  const title = document.querySelector("#title-input").value.trim();
  if (!title) { toast("书名不能为空。"); return; }
  if (!apiAvailable || !book) {
    book.title = title;
    hideModal("#title-modal");
    updateTopState();
    renderBooks();
    toast(`书名已更新为《${title}》。`);
    return;
  }
  try {
    const work = await apiRequest(`/stories/${book.id}/title`, { method: "PUT", body: JSON.stringify({ title, expected_version: book.version || 1 }) });
    book.title = work.title;
    book.version = work.version;
    hideModal("#title-modal");
    updateTopState();
    renderBooks();
    toast(`书名已更新为《${book.title}》。`);
  } catch (error) {
    toast("保存失败：版本冲突或后端不可用，请刷新后重试。");
  }
}

function updateTopState() {
  const crumb = document.querySelector("#crumb");
  const stepbar = document.querySelector("#stepbar");
  const book = currentBook();
  const inLibrary = document.querySelector("#works").classList.contains("active");
  if (!book || inLibrary) {
    crumb.innerHTML = `<span>作品库</span>`;
    stepbar.classList.add("library-only");
    return;
  }
  crumb.innerHTML = `<strong>${book.title}</strong><span class="status-dot">${book.status === "completed" ? "已完成" : "进行中"}</span><button class="title-edit" type="button" data-title-edit aria-label="修改书名">✎</button>`;
  stepbar.classList.remove("library-only");
  updateStepbarLock();
}

function renderBooks() {
  const grid = document.querySelector("#book-grid");
  if (!books.length) {
    grid.innerHTML = `<div class="books-empty"><h3>还没有作品</h3><p>点击“新建故事”，从一句创作意图开始。</p><button class="primary-button" type="button" id="new-book">＋ 新建故事</button></div>`;
    return;
  }
  grid.innerHTML = books.map((book) => `
    <article class="book-card" data-id="${book.id}">
      <button class="book-cover ${book.status}" type="button" data-open="${book.id}" style="background:linear-gradient(160deg, ${book.cover[0]} 0%, ${book.cover[1]} 78%)">
        <span class="book-spine"></span>
        <span class="book-status ${book.status}">${book.status === "completed" ? "✓ 已完成" : "● 进行中"}</span>
        <span class="book-title">${book.title}</span>
        <span class="book-subtitle">${book.stage === "idea" ? "尚未分类 · 待生成" : "创作中 · 进行中"}</span>
      </button>
      <div class="book-meta">
        <h3>${book.title}</h3>
        <p>${book.progress}</p>
        <div class="book-meta-foot"><span>更新于 ${book.updated}</span><button class="delete-book" type="button" data-id="${book.id}" aria-label="删除 ${book.title}">删除</button></div>
      </div>
    </article>`).join("");
}

async function createNewBook() {
  const n = books.length + 1;
  if (apiAvailable) {
    try {
      const work = await apiRequest("/works", { method: "POST", body: JSON.stringify({ title: `未命名故事 ${n}` }) });
      books.unshift(apiWorkToBook(work));
      activeBook = work.id;
      renderBooks();
      showScreen("idea");
      toast("已创建新故事，请写下创作意图。");
      return;
    } catch (error) {
      toast("后端暂不可用，已使用本地原型数据继续。");
    }
  }
  books.unshift({ id: "b" + Date.now(), title: `未命名故事 ${n}`, subtitle: "尚未分类 · 待生成", status: "inprogress", progress: "尚未开始", cover: ["#3f6db5", "#141f33"], updated: "刚刚", stage: "idea", idea: "" });
  activeBook = books[0].id;
  renderBooks();
  showScreen("idea");
  toast("已创建新故事，请写下创作意图。");
}
function renderIdea() {
  const book = currentBook();
  const editable = !!(book && book.stage === "idea");
  const input = document.querySelector("#idea-input");
  input.value = book ? (book.idea || "") : "";
  input.readOnly = !editable;
  input.disabled = !editable;
  document.querySelector("#idea-count").textContent = `${input.value.length} / 2,000`;
  document.querySelector("#idea-actions").style.display = editable ? "" : "none";
  document.querySelector("#show-write-tips").style.display = editable ? "" : "none";
  const tag = document.querySelector("#idea-tag");
  tag.textContent = editable ? "作者原文 · 可编辑" : "已锁定 · 只读";
  tag.classList.toggle("amber", !editable);
  document.querySelector("#idea-status").textContent = editable ? "一句话也好，一页设想也好。" : "概念已经生成，原始创意仅作浏览，不再改动。";
}
function showModal(selector) {
  const el = document.querySelector(selector);
  el.hidden = false;
  el.style.display = "grid";
  document.body.style.overflow = "hidden";
}

function hideModal(selector) {
  const el = document.querySelector(selector);
  el.hidden = true;
  el.style.display = "none";
  document.body.style.overflow = "";
}

async function openHistory(kind, index) {
  const entry = blueprintData[kind].entries[index];
  document.querySelector("#history-title").textContent = `更新履历 · ${entry.name}`;
  document.querySelector("#history-subtitle").textContent = `${blueprintData[kind].title} · 当前为最新版本 v${entry.version}`;
  let history = entry.history || [];
  if (apiAvailable && currentBook()) {
    try {
      if (kind === "living") {
        const versions = await apiRequest(`/stories/${currentBook().id}/living-state/history`);
        if (Array.isArray(versions) && versions.length) {
          history = versions.map((v) => {
            const confirmed = (v.payload && v.payload.confirmed_deltas) || [];
            const domains = (v.payload && v.payload.domains) || {};
            const cCount = (domains.characters?.state?.entries || []).length;
            const wCount = (domains.world?.state?.entries || []).length;
            const tCount = (domains.timeline?.state?.entries || []).length;
            const ch = v.version === 1 ? "初始投影（蓝图确认）" : `第 ${v.payload?.last_confirmed_chapter ?? "?"} 章 Delta 确认`;
            const detail = v.version === 1
              ? `Living State v${v.version}：由已确认 Blueprint 投影初始世界状态（角色 ${cCount} / 世界 ${wCount} / 时间线 ${tCount} 条）。`
              : `本章确认后投影：已确认 Delta ${confirmed.length} 条（角色 ${cCount} / 世界 ${wCount} / 时间线 ${tCount} 条）。`;
            return { version: `v${v.version}`, date: (v.updated_at || "").slice(0, 10) || "刚刚", by: "系统投影", note: ch, detail };
          });
        }
      } else if (["characters", "world", "timeline", "arc"].includes(kind)) {
        // 蓝图分类的更新履历：从后端加载该分类全部版本（含 AI 自动应用记录）。
        const versions = await apiRequest(`/stories/${currentBook().id}/blueprint/${kind}/history`);
        if (Array.isArray(versions) && versions.length) {
          history = versions.map((v) => {
            const payload = v.payload || {};
            const aiUpdates = payload._ai_updates || [];
            const entryCount = (payload.entries || []).length;
            let note, detail;
            if (v.version === 1) {
              note = "初始生成";
              detail = `${blueprintData[kind].title} v${v.version}：初始候选（${entryCount} 条）。`;
            } else if (aiUpdates.length) {
              const last = aiUpdates[aiUpdates.length - 1];
              const total = aiUpdates.reduce((n, u) => n + (u.count || 0), 0);
              note = `第 ${last.chapter_ordinal ?? "?"} 章 · AI 自动应用 ${last.count || 0} 条`;
              detail = `本版本累计更新 ${total} 条：${(last.items || []).map((i) => `${i.action === "add" ? "新增" : "修改"}「${i.target}」`).join("、")}。`;
            } else {
              note = v.status === "confirmed" ? "作者确认" : "重新生成候选";
              detail = `${blueprintData[kind].title} v${v.version}：${entryCount} 条。`;
            }
            return { version: `v${v.version}`, date: (v.updated_at || "").slice(0, 10) || "刚刚", by: v.status === "confirmed" ? "作者/系统" : "AI", note, detail };
          });
        }
      }
    } catch (error) {
      // History endpoint unavailable: keep the current single entry.
    }
  }
  document.querySelector("#history-list").innerHTML = history.map((item) => `
    <div class="history-item">
      <div class="history-head"><span class="tag blue">${item.version}</span><b>${item.note}</b><small>${item.date} · ${item.by}</small></div>
      <p>${item.detail}</p>
    </div>`).join("");
  showModal("#history-modal");
}

function openDelete(id) {
  pendingDeleteId = id;
  const book = books.find((item) => item.id === id);
  document.querySelector("#confirm-text").textContent = `确定要删除《${book.title}》吗？作品数据、章节规划、生成记录与状态快照都会被移除，此操作不可恢复。`;
  showModal("#confirm-modal");
}

function closeDelete() {
  pendingDeleteId = null;
  hideModal("#confirm-modal");
}

function openConfig() {
  const apply = (config) => {
    aiConfig = { model: config.model, temperature: config.temperature, reasoning: config.reasoning_strength || config.reasoning, version: config.version || 1 };
    document.querySelector("#config-model").value = aiConfig.model;
    document.querySelector("#config-temp").value = aiConfig.temperature;
    document.querySelector("#config-temp-value").textContent = aiConfig.temperature;
    document.querySelector("#config-reasoning").value = aiConfig.reasoning;
    showModal("#config-modal");
  };
  const book = currentBook();
  // 先用本地缓存立即打开弹窗，避免等待网络；随后异步刷新真实配置
  apply(aiConfig);
  if (apiAvailable && book) {
    apiRequest(`/stories/${book.id}/ai-config`).then(apply).catch(() => {});
  }
  // 模型可用性：未探测过则异步加载，否则按最新结果重建下拉（不可用模型置为禁用）
  if (modelAvailability === null) {
    loadModelAvailability();
  } else {
    populateModelSelect(true);
  }
}

async function loadModelAvailability() {
  if (!apiAvailable) {
    modelAvailability = [];
    populateModelSelect();
    return;
  }
  try {
    const list = await apiRequest("/models/availability", { timeoutMs: 10000 });
    modelAvailability = Array.isArray(list) ? list : [];
  } catch (error) {
    modelAvailability = [];
  }
  populateModelSelect();
}

// 用探测结果重建 #config-model 下拉；不可用模型 disabled；当前模型不可用时回退到首个可用项
function populateModelSelect(notify = false) {
  const select = document.querySelector("#config-model");
  if (!select) return;
  const current = aiConfig.model;
  const specs = modelAvailability && modelAvailability.length
    ? modelAvailability
    : [
        { provider: "deepseek", name: "DeepSeek V4 Flash", available: true },
        { provider: "agnes", name: "Agnes 2.5 Flash", available: true },
        { provider: "grok", name: "Grok 4.5", available: true },
        { provider: "ollama", name: "Qwen3.6 Abliterated 27B (Ollama)", available: true },
      ];
  select.replaceChildren(...specs.map((m) => {
    const opt = document.createElement("option");
    opt.value = m.name;
    opt.textContent = m.available ? m.name : `${m.name}（离线 · 不可用）`;
    opt.disabled = !m.available;
    return opt;
  }));
  const enabled = specs.filter((m) => m.available).map((m) => m.name);
  if (enabled.includes(current)) {
    select.value = current;
  } else if (enabled.length) {
    select.value = enabled[0];
    if (notify) toast(`模型「${current}」当前不可用，已回退到「${enabled[0]}」。`);
  }
}

function renderChapters() {
  document.querySelector("#chapter-grid").innerHTML = chapters.map(([no, title, text, state]) => `
    <article class="chapter-card ${state}">
      <span class="chapter-number">CHAPTER ${no}</span>
      <span class="tag ${state === "active" ? "blue" : ""}">${state === "active" ? "可进入 · 当前章" : "🔒 未激活 · 雏形"}</span>
      <h3>${title}</h3><p>${text}</p>
      <button class="${state === "active" ? "primary-button" : "secondary-button"}" type="button" ${state === "active" ? "data-nav=\"workspace\"" : "data-toast=\"后序章节保持为计划雏形，完成并确认当前章 Delta 后才会激活。\""}>${state === "active" ? "进入工作台 →" : "查看计划雏形"}</button>
    </article>`).join("");
}

function renderChaptersEmpty() {
  document.querySelector("#chapter-grid").innerHTML = `<div class="books-empty" style="grid-column:1/-1"><h3>尚未生成章节雏形</h3><p>确认 Blueprint 后，点击右上角「生成章节雏形」，AI 将根据蓝图生成章节卡片并只激活第 1 章。</p></div>`;
  const summary = document.querySelector(".chapter-summary");
  if (summary) {
    const first = summary.firstElementChild;
    if (first) first.innerHTML = `<b>0 章</b><span>·</span>尚未生成章节计划`;
    const groups = summary.querySelectorAll("div");
    if (groups[1]) groups[1].innerHTML = `<span class="tag blue">等待生成</span><span class="tag">生成后第 1 章激活</span>`;
  }
}

async function loadChaptersForCurrentStory() {
  const book = currentBook();
  if (!apiAvailable || !book) return;
  try {
    const response = await apiRequest(`/stories/${book.id}/chapters`);
    if (response.length) {
      window.currentChapters = response;
      renderChaptersFromApi(response);
    } else {
      window.currentChapters = [];
      const note = document.querySelector("#chapter-plan-note");
      if (note) note.textContent = book.stage === "blueprint_confirmed" || book.stage === "chapter_planning" ? "蓝图已确认 · 可生成章节雏形" : "等待蓝图确认";
      renderChaptersEmpty();
    }
  } catch (error) {
    window.currentChapters = [];
    renderChaptersEmpty();
  }
}

function renderChaptersFromApi(items) {
  const active = items.find((chapter) => chapter.access_status === "active");
  const note = document.querySelector("#chapter-plan-note");
  if (note) note.textContent = active ? `已生成 · 第 ${active.ordinal} 章已激活` : "已生成章节计划";
  document.querySelector("#chapter-grid").innerHTML = items.map((chapter) => {
    const isActive = chapter.access_status === "active";
    const done = chapter.access_status === "completed";
    const statusClass = isActive ? "blue" : done ? "green" : "";
    const statusText = isActive ? "可进入 · 当前章" : done ? "✓ 已完成" : "🔒 未激活 · 雏形";
    const btnClass = isActive ? "primary-button" : "secondary-button";
    const btnText = isActive ? "进入工作台 →" : done ? "查看已完成章节" : "查看计划雏形";
    const btnAction = isActive ? "data-nav=\"workspace\"" : done ? `data-chapter-id="${chapter.id}"` : "data-toast=\"后序章节保持锁定，完成当前章并确认 Chapter Delta 后才会激活。\"";
    return `<article class="chapter-card ${isActive ? "active" : done ? "done" : "locked"}">
      <span class="chapter-number">CHAPTER ${String(chapter.ordinal).padStart(2, "0")}</span>
      <span class="tag ${statusClass}">${statusText}</span>
      <h3>${chapter.title}</h3><p>${chapter.goal || chapter.summary}</p>
      <button class="${btnClass}" type="button" ${btnAction}>${btnText}</button>
    </article>`;
  }).join("");
  const doneCount = items.filter((chapter) => chapter.access_status === "completed").length;
  if (active) document.querySelector(".chapter-summary").firstElementChild.innerHTML = `<b>${items.length} 章</b><span>·</span>${doneCount ? `已完成 ${doneCount} 章 · ` : ""}当前计划 · 第 ${active.ordinal} 章已激活`;
}

function beatHtml([name, state, content, type], index) {
  const isCurrent = type === "current";
  const canGenerate = isCurrent && !generatedBeat;
  const body = generatedBeat && isCurrent
    ? "林墨用纸质归档与系统索引逐页对照，发现替换者刻意留下了一个仅内部人员才会使用的校验标记。他无法从中判断身份，却确认这不是程序错误。"
    : content;
  const statusClass = type === "done" ? "green" : type === "current" ? "blue" : "";
  const statusText = generatedBeat && isCurrent ? "已生成候选" : state;
  return `<article class="beat-card ${isCurrent ? "current" : ""}">
    <button class="beat-head" type="button" aria-expanded="${isCurrent}"><span class="tag ${statusClass}">${statusText}</span><b>${name}</b><span>${isCurrent ? "收起 ▴" : "展开 ▾"}</span></button>
    <div class="beat-body" ${isCurrent ? "" : "hidden"}>${body}</div>
    <div class="beat-actions">${type === "done" ? "<button class=\"secondary-button\" type=\"button\" data-toast=\"原正文版本会保留；重生成会创建一个新候选版本。\">重新生成</button>" : canGenerate ? "<button class=\"secondary-button\" type=\"button\" data-toast=\"原型仅演示当前 Beat 的顺序生成。\">调整计划</button><button class=\"primary-button generate-beat\" type=\"button\">生成 Beat 正文 →</button>" : isCurrent ? "<button class=\"secondary-button\" type=\"button\" data-toast=\"候选正文尚未应用；作者应用后才会创建 Beat 检查点。\">应用候选正文</button>" : "<button class=\"secondary-button\" type=\"button\" disabled>等待前序 Beat</button>"}</div>
  </article>`;
}

// --- Phase 5/6: real API workspace rendering ---

function beatHtmlApi(beat, readOnly) {
  const prose = beat.latest_prose;
  const finished = beat.status === "applied" || beat.status === "completed";
  const statusText = finished ? "✓ 已完成" : beat.status === "generated" ? "已生成" : beat.status === "available" ? "当前 Beat" : beat.status === "planned" ? "计划中" : beat.status;
  const statusClass = finished ? "green" : beat.status === "generated" ? "purple" : beat.status === "available" ? "blue" : "";
  const body = prose ? prose.markdown : (beat.instruction || "（暂无节拍指令。）");
  const expanded = finished || beat.status === "generated" || beat.status === "available";
  const versionBadge = prose ? `<span class="tag" style="margin-left:8px">v${prose.version}</span>` : "";
  let actions = "";
  if (readOnly) {
    actions = `<span class="tag green" style="margin-left:8px">已应用 v${prose ? prose.version : "?"}</span>`;
  } else if (prose) {
    actions = `<button class="secondary-button edit-beat" type="button" data-scene-id="${beat.scene_id}" data-beat-id="${beat.id}">✎ 编辑正文</button> <button class="secondary-button regenerate-beat" type="button" data-scene-id="${beat.scene_id}" data-beat-id="${beat.id}">重新生成</button>${versionBadge}`;
  } else {
    actions = `<button class="primary-button generate-beat" type="button" data-scene-id="${beat.scene_id}" data-beat-id="${beat.id}" data-beat-name="${(beat.name || `Beat ${beat.ordinal}`).replace(/"/g, "&quot;")}">生成 Beat 正文 →</button> <button class="secondary-button edit-beat" type="button" data-scene-id="${beat.scene_id}" data-beat-id="${beat.id}">✎ 作者手写</button>`;
  }
  return `<article class="beat-card ${beat.status === "available" || beat.status === "generated" || finished ? "current" : ""}">
    <button class="beat-head" type="button" aria-expanded="${expanded}"><span class="tag ${statusClass}">${statusText}</span><b>${beat.name || `Beat ${beat.ordinal}`}</b><span>${expanded ? "收起 ▴" : "展开 ▾"}</span></button>
    <div class="beat-body" ${expanded ? "" : "hidden"}>${body}</div>
    <div class="beat-actions">${actions}</div>
  </article>`;
}

function renderWorkspaceFromContext(context) {
  const chapter = context.chapter;
  const scenesData = context.scenes || [];
  const readOnly = chapter.access_status === "completed";
  // Chapter-wide missing prose count (any beat without an applied version).
  const chapterMissing = scenesData.reduce((n, s) => n + (s.beats || []).filter((b) => b.status !== "applied" && b.status !== "completed" && !(b.latest_prose && b.latest_prose.status === "applied")).length, 0);
  const wsHeading = document.querySelector(".workspace-heading .title-with-actions h1");
  if (wsHeading) wsHeading.textContent = `Chapter ${String(chapter.ordinal).padStart(2, "0")} · ${chapter.title || ""}${readOnly ? "（已完成）" : ""}`;
  document.querySelector(".rail-head h3").textContent = chapter.title || `第 ${chapter.ordinal} 章`;
  document.querySelector(".rail-head b").textContent = `CHAPTER ${String(chapter.ordinal).padStart(2, "0")}`;
  // Read-only completed chapters: offer a chapter-level backfill when prose is missing.
  const backfillBtn = readOnly && chapterMissing > 0
    ? `<button class="secondary-button backfill-chapter" type="button" style="margin:8px 12px 4px;width:calc(100% - 24px)">补全本章缺失正文（${chapterMissing} 段）→</button>`
    : "";
  const railFooter = document.querySelector(".rail-footer");
  if (railFooter) railFooter.innerHTML = backfillBtn + `<button class="text-button" type="button" id="show-context">▣ 查看 Chapter Context</button>`;
  const railGoal = document.querySelector(".rail-head p");
  if (railGoal) railGoal.textContent = chapter.goal ? `目标：${chapter.goal}` : "";
  // Disable the top-level "generate whole chapter" button in read-only mode.
  const completeBtn = document.querySelector("#complete-chapter");
  if (completeBtn) completeBtn.disabled = readOnly;

  if (!scenesData.length) {
    document.querySelector("#scene-items").innerHTML = "";
    document.querySelector("#active-scene-label").textContent = "尚无场景计划";
    document.querySelector("#editor-status").textContent = readOnly ? "已完成" : "等待生成";
    const actionButton = readOnly ? "" : `<button class="primary-button generate-scene-plan" type="button">生成场景计划 →</button>`;
    document.querySelector("#scene-content").innerHTML = `<div class="scene-title-row"><h2 class="scene-title">${readOnly ? "该章节已完成" : "尚未生成场景计划"}</h2>${actionButton}<button class="config-button" type="button" data-config>⚙ 生成设置</button></div><p class="scene-subtitle">${readOnly ? "本章已确认 Delta 并完成写作，仅可查看历史。" : "先为本章规划 Scene，再逐场景规划 Beat。"}</p><div class="scene-overview"><b>Chapter 目标</b><br>${chapter.goal || chapter.summary || "暂无"}</div>`;
    bindWorkspaceEvents();
    return;
  }

  if (!scenesData.some((scene) => scene.id === activeScene)) activeScene = scenesData[0].id;
  document.querySelector("#scene-items").innerHTML = scenesData.map((scene) => {
    const isCurrent = scene.id === activeScene;
    return `<button class="scene-item ${isCurrent ? "current" : ""} ${scene.status === "completed" ? "done" : ""}" type="button" data-scene="${scene.id}">${scene.status === "completed" ? "✓ " : ""}Scene ${scene.ordinal} · ${scene.title || ""}<small>${scene.status === "available" ? "当前" : scene.status === "planned" ? "计划中" : scene.status} · ${(scene.beats || []).length} 个 Beat</small></button>`;
  }).join("");

  const scene = scenesData.find((item) => item.id === activeScene) || scenesData[0];
  const subtitle = [scene.location, scene.time, scene.pov].filter(Boolean).join(" · ");
  document.querySelector("#active-scene-label").textContent = `Scene ${scene.ordinal} · ${scene.title}`;
  document.querySelector("#editor-status").textContent = scene.status === "available" ? "当前 Scene" : scene.status === "completed" ? "已完成" : "计划中";
  const beats = scene.beats || [];
  const beatsHtml = beats.map((b) => beatHtmlApi(b, readOnly)).join("");
  // Chapter Delta 的完整性是章节级约束，不能只看当前选中的 Scene。
  const chapterBeats = scenesData.flatMap((item) => item.beats || []);
  const allBeatsDone = chapterBeats.length > 0 && chapterBeats.every((b) => b.status === "applied" || b.status === "completed");
  const missingBeatCount = chapterBeats.filter((b) => b.status !== "applied" && b.status !== "completed").length;
  const actionBar = readOnly
    ? ""
    : `<button class="secondary-button generate-beat-plan" type="button" data-scene-id="${scene.id}">生成节拍计划 →</button> <button class="secondary-button generate-chapter-remaining" type="button">完成本章剩余 →</button>`;
  const deltaArea = (!readOnly && allBeatsDone)
    ? `<div class="scene-actions delta-confirm-area" style="margin-top:16px;padding:14px;border:1px solid var(--accent,#7c5cff);border-radius:10px"><b>Chapter Delta 就绪</b><p style="margin:6px 0">本章所有 Beat 已应用。确认 Chapter Delta 后将更新 Living State 并激活下一章。</p><button class="primary-button confirm-chapter-delta" type="button">确认 Chapter Delta →</button></div>`
    : (!readOnly && missingBeatCount ? `<div class="scene-actions" style="margin-top:16px;padding:12px;border:1px solid rgba(229,182,90,.45);border-radius:10px"><b>Chapter Delta 尚未就绪</b><p style="margin:6px 0">本章仍有 ${missingBeatCount} 个 Beat 未完成。请完成全部 Scene 正文后再确认 Delta。</p></div>` : "");
  const sceneGenButton = readOnly ? "" : `<button class="primary-button scene-generate" type="button">生成整个 Scene 正文</button>`;
  document.querySelector("#scene-content").innerHTML = `<div class="scene-title-row"><h2 class="scene-title">Scene ${scene.ordinal} · ${scene.title}</h2>${sceneGenButton}<button class="config-button" type="button" data-config>⚙ 生成设置</button></div><p class="scene-subtitle">${subtitle}</p><div class="scene-overview"><b>Scene 描述</b><br>${scene.character_goals || ""}${scene.conflict ? `<br><b>冲突：</b>${scene.conflict}` : ""}${scene.key_events ? `<br><b>关键事件：</b>${scene.key_events}` : ""}${scene.scene_result ? `<br><b>场景结果：</b>${scene.scene_result}` : ""}${scene.summary ? `<br><b>场景摘要：</b>${scene.summary}` : ""}</div>${beatsHtml || `<div class="books-empty" style="grid-column:1/-1"><h3>该场景尚未规划 Beat</h3><p>点击下方「生成节拍计划」，为当前场景规划 Beat 顺序。</p></div>`}<div class="scene-actions" style="margin-top:12px">${actionBar}</div>${deltaArea}`;
  renderWorkspaceStatus(context);
  bindWorkspaceEvents();
}

function renderWorkspaceStatus(context) {
  const chapter = context.chapter;
  const snapshot = context.snapshot;
  const scenes = context.scenes || [];
  const doneScenes = scenes.filter((s) => s.status === "completed").length;
  const totalBeats = scenes.reduce((n, s) => n + (s.beats || []).length, 0);
  const doneBeats = scenes.reduce((n, s) => n + (s.beats || []).filter((b) => b.status === "applied" || b.status === "completed").length, 0);
  const readOnly = chapter.access_status === "completed";

  // Right status rail.
  const snapEl = document.querySelector("#snapshot-status");
  if (snapEl) snapEl.textContent = snapshot ? (snapshot.status === "valid" ? `有效 · Chapter ${String(chapter.ordinal).padStart(2, "0")} 入口` : "过期 · 需按序重算") : "未构建";
  const sceneEl = document.querySelector("#scene-status");
  if (sceneEl) sceneEl.textContent = scenes.length ? (doneScenes === scenes.length ? `已完成 ${doneScenes}/${scenes.length} 个场景` : `进行中 · ${doneBeats}/${totalBeats} Beat`) : "尚无场景计划";
  const deltaEl = document.querySelector("#delta-count");
  if (deltaEl) {
    const proposed = (context.deltas || []).filter((d) => d.status === "proposed").length;
    deltaEl.textContent = readOnly ? "已确认" : proposed ? `${proposed} 条 · 待确认` : "0 条 · 待确认";
  }
  const issueEl = document.querySelector("#issue-count");
  if (issueEl) {
    const open = (context.issues || []).filter((i) => i.status === "open").length;
    issueEl.textContent = open ? `${open} 条提醒 · 不阻止写作` : "0 条提醒";
  }

  // Global state modal: rebuild from real snapshot + events.
  const modalGrid = document.querySelector("#state-modal .state-modal-grid");
  if (!modalGrid) return;
  // Modal header must reflect the real entry chapter, never a static label.
  const eyebrowEl = document.querySelector("#state-modal .eyebrow");
  if (eyebrowEl) eyebrowEl.textContent = `LIVING STATE · CHAPTER ${String(chapter.ordinal).padStart(2, "0")} ENTRY`;
  const state = snapshot?.state || { characters: {}, world: {}, timeline: {} };

  const charEntries = Array.isArray(state.characters?.entries) ? state.characters.entries : [];
  const worldEntries = Array.isArray(state.world?.entries) ? state.world.entries : [];
  const timelineEntries = Array.isArray(state.timeline?.entries) ? state.timeline.entries : [];
  const events = context.events || [];

  // Format field values that may be nested objects / object arrays (e.g. timeline events).
  const fmt = (v) => Array.isArray(v)
    ? v.map((x) => typeof x === "object" && x !== null ? Object.entries(x).map(([k, val]) => `${k}：${val}`).join("，") : String(x)).join("；")
    : typeof v === "object" && v !== null ? Object.entries(v).map(([k, val]) => `${k}：${val}`).join("；") : String(v == null ? "" : v);
  const factHtml = (name, text, source) => `<div class="state-fact"><b>${name}</b><p>${text || "（暂无）"}</p>${source ? `<small>来源：${source}</small>` : ""}</div>`;
  const charFacts = charEntries.length ? charEntries.map((e) => factHtml(e.name || "角色", Object.values(e.fields || {}).map(fmt).join("；") || "已确认设定", `Living State · ${snapshot ? snapshot.status : ""}`)).join("") : `<div class="state-fact"><b>暂无角色状态</b><p>确认 Blueprint 后自动投影。</p></div>`;
  const worldFacts = worldEntries.length ? worldEntries.map((e) => factHtml(e.name || "世界条目", Object.values(e.fields || {}).map(fmt).join("；") || "已确认设定", "Living State · confirmed")).join("") : `<div class="state-fact"><b>暂无世界状态</b><p>确认 Blueprint 后自动投影。</p></div>`;
  const eventsHtml = events.length ? events.map((ev, i) => `<div class="event-line"><b>E${String(i + 1).padStart(2, "0")}</b><p>${ev.title || ev.goal}${ev.planned_result ? ` · 目标：${ev.planned_result}` : ""}<br><small>${ev.actual_result ? `actual：${ev.actual_result}` : "planned · 尚未写入 Story State"}</small></p></div>`).join("") : `<div class="state-fact"><b>暂无 Chapter Events</b><p>可在工作台规划章节事件。</p></div>`;
  const timelineFacts = timelineEntries.length ? timelineEntries.map((e) => factHtml(e.name || "时间线条目", Object.values(e.fields || {}).map(fmt).join("；") || "", "Story Arc · confirmed")).join("") : `<div class="state-fact"><b>暂无时间线状态</b><p>确认 Blueprint 后自动投影。</p></div>`;

  modalGrid.innerHTML = `
    <article><h3>角色状态</h3>${charFacts}</article>
    <article><h3>世界状态</h3>${worldFacts}<h3 class="events-title">Chapter Events · 计划</h3>${eventsHtml}</article>
    <article><h3>时间线与剧情线</h3>${timelineFacts}</article>`;
  const footTag = document.querySelector("#state-modal .modal-foot .tag");
  if (footTag) {
    const proposed = (context.deltas || []).filter((d) => d.status === "proposed").length;
    footTag.textContent = readOnly ? `本章 Delta 已确认 · Chapter ${chapter.ordinal} 完成` : proposed ? `${proposed} 条 Delta 候选，需章节完成后确认` : "暂无 Delta 候选";
  }
}

function renderWorkspaceFallback() {
  document.querySelector("#scene-items").innerHTML = scenes.map((scene) => `<button class="scene-item ${scene.status} ${scene.id === activeScene ? "current" : ""}" type="button" data-scene="${scene.id}" ${scene.status === "locked" ? "disabled" : ""}>${scene.status === "done" ? "✓ " : ""}Scene ${scene.id} · ${scene.name}<small>${scene.hint}</small></button>`).join("");
  const data = sceneContent[activeScene];
  document.querySelector("#active-scene-label").textContent = data.title;
  document.querySelector("#editor-status").textContent = activeScene === 2 ? "当前 Scene" : activeScene === 1 ? "已完成" : "计划中";
  document.querySelector("#scene-content").innerHTML = `<div class="scene-title-row"><h2 class="scene-title">${data.title}</h2><button class="primary-button scene-generate" type="button">一键生成整个 Scene</button><button class="config-button" type="button" data-config>⚙ 生成设置</button></div><p class="scene-subtitle">${data.subtitle}</p><div class="scene-overview"><b>Scene 描述</b><br>${data.overview}</div>${data.beats.map(beatHtml).join("")}`;
  bindWorkspaceEvents();
}

async function loadWorkspaceContext() {
  const book = currentBook();
  if (!apiAvailable || !book) {
    currentWorkspaceContext = null;
    renderWorkspaceFallback();
    return;
  }
  // Show a loading placeholder instead of demo fallback while the context loads.
  document.querySelector(".rail-head h3").textContent = "加载章节上下文…";
  document.querySelector("#scene-content").innerHTML = `<div class="books-empty" style="grid-column:1/-1"><h3>正在装配 Chapter Context…</h3><p>Snapshot 与 Scene / Beat 计划正在加载。</p></div>`;
  document.querySelector("#scene-items").innerHTML = "";
  try {
    let chapterId = currentActiveChapterId;
    if (!chapterId) {
      const chapters = await apiRequest(`/stories/${book.id}/chapters`);
      const active = chapters.find((chapter) => chapter.access_status === "active");
      if (active) {
        chapterId = active.id;
      } else {
        // No active chapter (e.g. novel finished): fall back to the last-viewed
        // chapter, else the first chapter, so completed chapters stay readable.
        const saved = localStorage.getItem(`novel-ignite:last-chapter:${book.id}`);
        const savedChapter = chapters.find((c) => c.id === saved);
        chapterId = savedChapter ? savedChapter.id : (chapters[0] ? chapters[0].id : null);
      }
      currentActiveChapterId = chapterId;
    }
    if (!chapterId) {
      document.querySelector(".rail-head h3").textContent = "尚无激活章节";
      document.querySelector("#scene-content").innerHTML = `<div class="books-empty" style="grid-column:1/-1"><h3>尚未生成章节计划</h3><p>请先回到「章节规划」页生成章节雏形并激活第 1 章。</p></div>`;
      document.querySelector("#scene-items").innerHTML = "";
      return;
    }
    // Remember this chapter so the next workspace visit restores it.
    localStorage.setItem(`novel-ignite:last-chapter:${book.id}`, chapterId);
    let context = await apiRequest(`/stories/${book.id}/chapters/${chapterId}/context`, { timeoutMs: 60000 });
    // Phase 5/6 improvement: when entering the active chapter's workspace, auto-generate
    // the scene plan and beat plans in the loading phase — no manual click needed.
    const chapter = context.chapter;
    if (chapter && chapter.access_status === "active") {
      let autoGenerated = false;
      if (!context.scenes || !context.scenes.length) {
        autoGenerated = true;
        showThinking("正在自动生成场景计划…", "进入工作台时自动规划 Scene 顺序");
        try {
          await apiRequest(`/stories/${book.id}/chapters/${chapterId}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_scene_plan" }), timeoutMs: 300000 });
        } catch (e) { /* fall through; beat auto-gen below will re-check */ }
      }
      // Re-fetch so beat plans are created against real scenes.
      if (autoGenerated) {
        context = await apiRequest(`/stories/${book.id}/chapters/${chapterId}/context`, { timeoutMs: 60000 });
      }
      const scenes = context.scenes || [];
      const pendingBeatScenes = scenes.filter((s) => !s.beats || !s.beats.length);
      if (pendingBeatScenes.length) {
        autoGenerated = true;
        showThinking("正在自动生成节拍计划…", `为 ${pendingBeatScenes.length} 个场景规划 Beat 顺序`);
        for (let i = 0; i < pendingBeatScenes.length; i += 1) {
          const scene = pendingBeatScenes[i];
          setThinkingProgress(i, pendingBeatScenes.length, `Scene ${i + 1} / ${pendingBeatScenes.length} · ${scene.title || "未命名场景"}`);
          try {
            await apiRequest(`/stories/${book.id}/chapters/${chapterId}/scenes/${scene.id}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_beat_plan" }), timeoutMs: 300000 });
          } catch (e) { /* keep going */ }
        }
        setThinkingProgress(null);
      }
      if (autoGenerated) {
        context = await apiRequest(`/stories/${book.id}/chapters/${chapterId}/context`, { timeoutMs: 60000 });
        // Auto-generation finished; dismiss the thinking overlay before rendering.
        setThinkingProgress(null);
        hideThinking();
      }
    }
    let deltas = [];
    let issues = [];
    try {
      const [d, i] = await Promise.all([
        apiRequest(`/stories/${book.id}/chapters/${chapterId}/deltas`, { timeoutMs: 60000 }),
        apiRequest(`/stories/${book.id}/chapters/${chapterId}/issues`, { timeoutMs: 60000 }),
      ]);
      deltas = d || [];
      issues = i || [];
    } catch (e) { /* status panel degrades gracefully */ }
    context.deltas = deltas;
    context.issues = issues;
    currentWorkspaceContext = context;
    renderWorkspaceFromContext(context);
  } catch (error) {
    setThinkingProgress(null);
    hideThinking();
    currentWorkspaceContext = null;
    renderWorkspaceFallback();
  }
}

function renderWorkspace() {
  if (currentWorkspaceContext) {
    renderWorkspaceFromContext(currentWorkspaceContext);
  } else {
    renderWorkspaceFallback();
  }
}

// ---------------------------------------------------------------------------
// Phase 6+: reading mode (step 6) — continuous novel, Scene as section anchors
// ---------------------------------------------------------------------------

async function loadReaderForCurrentStory() {
  const book = currentBook();
  if (!apiAvailable || !book) return;
  const content = document.querySelector("#reader-content");
  content.innerHTML = `<div class="reader-empty"><h3>正在装载小说…</h3><p>正在汇编各章正文与场景。</p></div>`;
  try {
    readerData = await apiRequest(`/stories/${book.id}/read`, { timeoutMs: 60000 });
    const chapters = readerData.chapters || [];
    if (!chapters.length || !chapters.some((c) => (c.scenes || []).some((s) => (s.beats || []).length))) {
      content.innerHTML = `<div class="reader-empty"><h3>尚无正文可读</h3><p>完成章节写作并确认 Chapter Delta 后，正文会在此以连贯小说呈现。</p></div>`;
      renderReaderToc(chapters);
      document.querySelector("#read-status").textContent = "写作中 · 尚未完结";
      document.querySelector("#read-status").className = "tag";
      return;
    }
    // First chapter with any prose becomes the initial view.
    const firstWithProse = chapters.find((c) => (c.scenes || []).some((s) => (s.beats || []).length)) || chapters[0];
    readerActiveChapter = firstWithProse.id;
    readerActiveScene = null;
    renderReaderToc(chapters);
    renderReaderChapter(firstWithProse);
    const done = chapters.length && chapters.every((c) => c.access_status === "completed");
    document.querySelector("#read-status").textContent = done ? "已完成 · 全书完结" : "写作中 · 部分完成";
    document.querySelector("#read-status").className = done ? "tag blue" : "tag";
  } catch (error) {
    content.innerHTML = `<div class="reader-empty"><h3>阅读内容加载失败</h3><p>请稍后重试。</p></div>`;
  }
}

function renderReaderToc(chapters) {
  const list = document.querySelector("#reader-toc-list");
  document.querySelector("#reader-chapter-count").textContent = `${chapters.length} 章`;
  if (!chapters.length) { list.innerHTML = `<div class="reader-empty" style="padding:16px 8px"><p>暂无章节</p></div>`; return; }
  list.innerHTML = chapters.map((c) => {
    const allScenes = c.scenes || [];
    const written = allScenes.reduce((n, s) => n + (s.beats || []).length, 0);
    const writtenScenes = allScenes.filter((s) => (s.beats || []).length).length;
    const done = c.access_status === "completed";
    // Scene list: every scene as a row with its literary title; unwritten scenes show a hint.
    const sceneRows = allScenes.map((s) => {
      const has = (s.beats || []).length > 0;
      const count = (s.beats || []).length;
      return `<button class="reader-scene-row ${c.id === readerActiveChapter && s.id === readerActiveScene ? "current" : ""}" type="button" data-read-scene="${c.id}|${s.id}">
        <span class="reader-scene-no">${s.ordinal}</span>
        <span class="reader-scene-title">${escapeHtml(s.title || `场景 ${s.ordinal}`)}</span>
        ${has ? `<span class="reader-scene-count">${count} 段</span>` : `<span class="reader-scene-missing">未写作</span>`}
      </button>`;
    }).join("");
    return `<div class="reader-chapter-block ${c.id === readerActiveChapter ? "active" : ""}">
      <button class="reader-chapter-link" type="button" data-read-chapter="${c.id}">
        <b>第 ${c.ordinal} 章 · ${escapeHtml(c.title || "未命名")}</b>
        <small style="color:${done ? "#4ade80" : "#8fa6c8"}">${done ? "✓ 已完成" : "进行中"} · 已写 ${written} 段 / ${writtenScenes} 个场景</small>
      </button>
      <div class="reader-scene-list">${sceneRows}</div>
    </div>`;
  }).join("");
}

function renderReaderChapter(chapter) {
  readerActiveChapter = chapter.id;
  const content = document.querySelector("#reader-content");
  const allScenes = chapter.scenes || [];
  const writtenScenes = allScenes.filter((s) => (s.beats || []).length);
  const beatsTotal = writtenScenes.reduce((n, s) => n + s.beats.length, 0);
  document.querySelector("#read-title").textContent = `${chapter.title || "未命名章节"}`;
  document.querySelectorAll(".reader-chapter-block").forEach((el) => {
    const link = el.querySelector("[data-read-chapter]");
    el.classList.toggle("active", link && link.dataset.readChapter === chapter.id);
  });
  if (!writtenScenes.length) {
    content.innerHTML = `<div class="reader-empty"><h3>本章暂无正文</h3><p>完成本章写作并确认 Delta 后即可阅读。</p></div>`;
    return;
  }
  const scenesHtml = allScenes.map((scene) => {
    const sub = [scene.location, scene.time].filter(Boolean).join(" · ");
    const has = (scene.beats || []).length > 0;
    if (!has) {
      return `<section class="reader-scene-section" id="scene-${chapter.id}-${scene.id}">
        <h3>${escapeHtml(scene.title || `场景 ${scene.ordinal}`)}</h3>${sub ? `<p class="reader-scene-sub">${escapeHtml(sub)}</p>` : ""}
        <div class="reader-scene-unwritten"><p>（本章节尚未写作正文）</p></div>
      </section>`;
    }
    const proseHtml = scene.beats.map((b) => `<div class="reader-prose"><p>${escapeHtml(b.markdown || "")}</p></div>`).join("");
    return `<section class="reader-scene-section" id="scene-${chapter.id}-${scene.id}">
      <h3>${escapeHtml(scene.title || `场景 ${scene.ordinal}`)}</h3>${sub ? `<p class="reader-scene-sub">${escapeHtml(sub)}</p>` : ""}
      ${scene.summary ? `<p class="reader-scene-summary"><b>场景摘要：</b>${escapeHtml(scene.summary)}</p>` : ""}
      ${proseHtml}
    </section>`;
  }).join("");
  content.innerHTML = `
    <h2>第 ${chapter.ordinal} 章 · ${escapeHtml(chapter.title || "未命名章节")}</h2>
    <p class="reader-chapter-meta">已写 ${beatsTotal} 段正文 · ${allScenes.length} 个场景（${writtenScenes.length} 个已写作）</p>
    ${scenesHtml}`;
  // Reset any pending scene anchor.
  readerActiveScene = null;
}

function readerScrollToScene(chapterId, sceneId) {
  if (chapterId !== readerActiveChapter) {
    const chapter = (readerData.chapters || []).find((c) => c.id === chapterId);
    if (chapter) renderReaderChapter(chapter);
  }
  readerActiveScene = sceneId;
  document.querySelectorAll(".scene-anchor").forEach((el) => el.classList.toggle("current", el.dataset.readScene === `${chapterId}|${sceneId}`));
  // Immediate scroll is reliable in every environment (including headless).
  const el = document.getElementById(`scene-${chapterId}-${sceneId}`);
  if (!el) return;
  const currentY = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  const top = Math.max(0, el.getBoundingClientRect().top + currentY - 90);
  window.scrollTo(0, top);
  document.documentElement.scrollTop = top;
  document.body.scrollTop = top;
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

// ---------------------------------------------------------------------------
// Phase 8: paper book reading mode (step 8) — centered paper book with page turn
// ---------------------------------------------------------------------------

let bookPages = [];              // 分页后的全部书页
let bookIndex = 0;               // 当前右页索引（右页 = bookIndex，左页 = bookIndex - 1）
let bookTurning = false;         // 翻页动画锁
const BOOK_DEFAULT_SETTINGS = { fontSize: 19, lineHeight: 1.8, fontFamily: "serif", theme: "xuan" };
let bookSettings = { ...BOOK_DEFAULT_SETTINGS };

function loadBookSettings() {
  try {
    const raw = localStorage.getItem("novel-ignite:book-settings");
    if (raw) bookSettings = { ...BOOK_DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch (e) { bookSettings = { ...BOOK_DEFAULT_SETTINGS }; }
}

function saveBookSettings() {
  try { localStorage.setItem("novel-ignite:book-settings", JSON.stringify(bookSettings)); } catch (e) { /* ignore */ }
}

// 按字符容量分页：章首页 / 正文页。
// 短段落累积填充到一页（直到接近容量），超长段落单独切分续页；场景标题显示在该场景首页页头。
function paginateNovel(chapters) {
  const cap = bookCharsPerPage();
  const pages = [];
  let chapterMeta = null;       // { no, title } 当前章节
  let buf = [];                 // 当前页待结算的文本行
  let bufLen = 0;
  let headForNext = null;       // 下一页页头要显示的 { sceneTitle, sceneSub }

  function flush() {
    if (!buf.length) return;
    pages.push({
      kind: "prose",
      chapterNo: chapterMeta ? chapterMeta.no : 0,
      chapterTitle: chapterMeta ? chapterMeta.title : "",
      sceneTitle: headForNext ? headForNext.sceneTitle : "",
      sceneSub: headForNext ? headForNext.sceneSub : "",
      text: buf.join("\n"),
    });
    buf = [];
    bufLen = 0;
    headForNext = null;
  }

  for (const ch of chapters) {
    const scenes = ch.scenes || [];
    let headPushed = false;
    for (const sc of scenes) {
      const beats = (sc.beats || []).filter((b) => b.markdown);
      if (!beats.length) continue;
      if (!headPushed) {
        flush();
        pages.push({ kind: "chapter", chapterNo: ch.ordinal, chapterTitle: ch.title || "未命名", text: "" });
        headPushed = true;
        chapterMeta = { no: ch.ordinal, title: ch.title || "未命名" };
      }
      const sceneLabel = sc.title || `场景 ${sc.ordinal}`;
      const sceneSub = [sc.location, sc.time].filter(Boolean).join(" · ");
      let sceneHeadDone = false;
      for (const b of beats) {
        const paras = String(b.markdown || "").split(/\n+/)
          .map((s) => s.trim())
          // 剔除 markdown 标题行（页头已显示场景标题，避免「同一标题出现两次」）
          .filter((s) => s && !/^#{1,6}\s+/.test(s))
          .map((s) => s.replace(/^\>+\s?/, "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/\*(.+?)\*/g, "$1"))
          .filter(Boolean);
        for (const raw of paras) {
          if (!sceneHeadDone) {
            if (buf.length) flush();      // 当前页已有内容则开新页承载场景标题
            headForNext = { sceneTitle: sceneLabel, sceneSub };
            sceneHeadDone = true;
          }
          let rest = raw;
          while (rest.length > cap) {
            flush();
            pages.push({
              kind: "prose",
              chapterNo: chapterMeta ? chapterMeta.no : 0,
              chapterTitle: chapterMeta ? chapterMeta.title : "",
              sceneTitle: headForNext ? headForNext.sceneTitle : "",
              sceneSub: headForNext ? headForNext.sceneSub : "",
              text: rest.slice(0, cap),
            });
            rest = rest.slice(cap);
            headForNext = null;
          }
          if (!rest) continue;
          if (bufLen + rest.length > cap && buf.length) flush();
          buf.push(rest);
          bufLen += rest.length;
        }
      }
    }
  }
  flush();
  return pages;
}

function bookCharsPerPage() {
  // 实际书页尺寸：1320×930，右半页宽 660px
  const w = 660, h = 930;                  // 书页右半页视觉尺寸
  const padX = 124, padTop = 104, padBottom = 70;   // 左右内边距合计、上下内边距
  const fontSize = bookSettings.fontSize || 16;
  const lineHeight = bookSettings.lineHeight || 1.8;
  const lineH = Math.max(20, Math.round(fontSize * lineHeight));
  const charsPerLine = Math.max(10, Math.floor((w - padX) / fontSize));
  const linesPerPage = Math.max(5, Math.floor((h - padTop - padBottom) / lineH));
  
  // 考虑标题占用，预留4行空间
  const usableLines = Math.max(4, linesPerPage - 4);
  
  // 使用85%容量，平衡填充率和安全性
  return Math.floor(charsPerLine * usableLines * 0.85);
}

function bookThemeClass() {
  return "theme-" + (bookSettings.theme || "xuan");
}

function pageHtml(page) {
  const theme = bookThemeClass();
  if (!page) return `<div class="sheet-page ${theme} book-blank"><p>（空白页）</p></div>`;
  if (page.kind === "chapter") {
    return `<div class="sheet-page ${theme} chapter-page"><p class="page-chapter-no">第 ${page.chapterNo} 章</p><h1>${escapeHtml(page.chapterTitle || "")}</h1></div>`;
  }
  const sceneHead = page.sceneTitle
    ? `<h4 class="page-scene-title">${escapeHtml(page.sceneTitle)}</h4>${page.sceneSub ? `<p class="page-scene-sub">${escapeHtml(page.sceneSub)}</p>` : ""}`
    : "";
  return `<div class="sheet-page ${theme} prose-page">${sceneHead}<p>${escapeHtml(page.text || "")}</p></div>`;
}

function renderBookOpen() {
  const left = bookPages[bookIndex - 1] || null;
  const right = bookPages[bookIndex] || null;
  document.querySelector("#book-page-left").innerHTML = pageHtml(left);
  document.querySelector("#book-page-right").innerHTML = pageHtml(right);
  document.querySelector("#paper-book").classList.toggle("at-start", bookIndex <= 0);
  document.querySelector("#paper-book").classList.toggle("at-end", bookIndex >= bookPages.length - 1);
}

function updateBookIndicator() {
  const no = document.querySelector("#book-page-no");
  const total = document.querySelector("#book-page-total");
  if (no) no.textContent = bookIndex + 1;
  if (total) total.textContent = bookPages.length;
}

function bookTurnNext() {
  if (bookTurning || bookIndex >= bookPages.length - 1) return;
  bookTurning = true;
  const flip = document.querySelector("#book-flip");
  // 视觉翻页：正文立即刷新，只在右下角显示纸角翻起与阴影，避免整页文字翻转造成重影。
  flip.innerHTML = `<div class="flip-corner"></div>`;
  flip.classList.add("flip-next");
  bookIndex += 1;
  renderBookOpen();
  updateBookIndicator();
  requestAnimationFrame(() => flip.classList.add("turning"));
  setTimeout(() => { flip.classList.remove("flip-next", "turning"); bookTurning = false; }, 950);
}

function bookTurnPrev() {
  if (bookTurning || bookIndex <= 0) return;
  bookTurning = true;
  const flip = document.querySelector("#book-flip");
  // 同样只保留左侧纸角翻起的视觉残留，不复制或翻转正文文字。
  flip.innerHTML = `<div class="flip-corner"></div>`;
  flip.classList.add("flip-prev");
  bookIndex -= 1;
  renderBookOpen();
  updateBookIndicator();
  requestAnimationFrame(() => flip.classList.add("turning"));
  setTimeout(() => { flip.classList.remove("flip-prev", "turning"); bookTurning = false; }, 950);
}

function renderBookToc(chapters) {
  const list = document.querySelector("#book-toc-list");
  document.querySelector("#book-toc-count").textContent = `${chapters.length} 章`;
  if (!chapters.length) { list.innerHTML = `<div class="book-toc-empty"><p>暂无章节</p></div>`; return; }
  list.innerHTML = chapters.map((c) => {
    const written = (c.scenes || []).some((s) => (s.beats || []).length);
    return `<button class="book-toc-row" type="button" data-book-chapter="${c.id}">
      <span class="book-toc-no">第${String(c.ordinal).padStart(2, "0")}章</span>
      <span class="book-toc-title">${escapeHtml(c.title || "未命名")}</span>
      <span class="book-toc-dot ${written ? "" : "dim"}">${written ? "●" : "○"}</span>
    </button>`;
  }).join("");
}

function bookJumpToChapter(chapterId) {
  const chapters = readerData?.chapters || [];
  const idx = chapters.findIndex((c) => c.id === chapterId);
  if (idx < 0 || !bookPages.length) return;
  let target = -1;
  for (let i = 0; i < bookPages.length; i += 1) {
    if (bookPages[i].kind === "chapter" && bookPages[i].chapterNo === chapters[idx].ordinal) { target = i; break; }
  }
  if (target < 0) target = Math.min(bookIndex, bookPages.length - 1);
  bookIndex = target;
  renderBookOpen();
  updateBookIndicator();
}

function applyBookSettingsUi() {
  const root = document.querySelector(".book-layout");
  if (!root) return;
  root.style.setProperty("--bs-font-size", bookSettings.fontSize + "px");
  root.style.setProperty("--bs-line-height", String(bookSettings.lineHeight));
  root.style.setProperty("--bs-font-family", {
    serif: '"Songti SC","Noto Serif SC",serif',
    kai: '"KaiTi","STKaiti",serif',
    fang: '"FangSong","STFangsong",serif',
    hei: '"Heiti SC","Microsoft YaHei",sans-serif',
  }[bookSettings.fontFamily] || "serif");
  root.classList.remove("theme-xuan", "theme-parch", "theme-rice", "theme-celadon", "theme-night");
  root.classList.add("theme-" + (bookSettings.theme || "xuan"));
  document.querySelectorAll("#book-settings .book-opt-group").forEach((group) => {
    const key = group.dataset.setting;
    group.querySelectorAll("button").forEach((btn) => btn.classList.toggle("active", String(btn.dataset.v) === String(bookSettings[key])));
  });
  if (bookPages.length) {
    const keep = Math.min(bookIndex, Math.max(0, bookPages.length - 1));
    bookPages = paginateNovel(readerData?.chapters || []);
    bookIndex = Math.min(keep, Math.max(0, bookPages.length - 1));
    renderBookOpen();
    updateBookIndicator();
  }
}

async function loadBookForCurrentStory() {
  const book = currentBook();
  if (!apiAvailable || !book) return;
  document.querySelector("#book-page-right").innerHTML = `<div class="sheet-page ${bookThemeClass()} book-empty"><p>正在装配纸质书…</p></div>`;
  try {
    readerData = await apiRequest(`/stories/${book.id}/read`, { timeoutMs: 60000 });
    const chapters = readerData.chapters || [];
    if (!chapters.length || !chapters.some((c) => (c.scenes || []).some((s) => (s.beats || []).length))) {
      document.querySelector("#book-status").textContent = "尚无正文";
      document.querySelector("#book-status").className = "tag";
      renderBookToc(chapters);
      document.querySelector("#book-page-left").innerHTML = "";
      document.querySelector("#book-page-right").innerHTML = `<div class="sheet-page ${bookThemeClass()} book-empty"><p>完成章节写作并确认 Delta 后，即可在纸质书中阅读。</p></div>`;
      return;
    }
    document.querySelector("#book-title").textContent = `${book.title} · 实体书`;
    bookPages = paginateNovel(chapters);
    bookIndex = 0;
    applyBookSettingsUi();
    renderBookToc(chapters);
    renderBookOpen();
    updateBookIndicator();
    const done = chapters.length && chapters.every((c) => c.access_status === "completed");
    document.querySelector("#book-status").textContent = done ? "全书完结 · 可通读" : "部分完成";
    document.querySelector("#book-status").className = done ? "tag blue" : "tag";
  } catch (error) {
    document.querySelector("#book-page-right").innerHTML = `<div class="sheet-page ${bookThemeClass()} book-empty"><p>实体书加载失败，请稍后重试。</p></div>`;
  }
}

async function loadCoverForCurrentStory() {
  const book = currentBook();
  if (!apiAvailable || !book) return;
  try {
    const work = await apiRequest(`/works/${book.id}`);
    document.querySelector("#cover-title").textContent = work.title || "未命名作品";
    document.querySelector("#cover-author").textContent = work.stage === "done" ? "全书完结 · 封面待生成" : "创作中 · 封面待生成";
  } catch (e) {
    document.querySelector("#cover-title").textContent = book.title || "未命名作品";
  }
}

async function handleBackfillClick() {
  const book = currentBook();
  if (!apiAvailable || !book || !currentActiveChapterId) { toast("需要激活章节。"); return; }
  showThinking("正在补全本章缺失正文…", "使用本章入口 Snapshot 作为上下文，避免与后续章节错乱");
  try {
    const result = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/backfill`, { method: "POST", body: JSON.stringify({ action: "generate_scene" }), timeoutMs: 600000 });
    const n = (result.prose_versions || []).length;
    currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
    renderWorkspace();
    toast(n ? `已补全 ${n} 段缺失正文（基于本章入口快照生成，后续章节已标记待重算）。` : "本章已无缺失正文。");
  } catch (error) {
    setThinkingProgress(null);
    try {
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      renderWorkspace();
    } catch (e) { /* keep previous render */ }
    toast("补全失败，请稍后重试。");
  }
  finally { hideThinking(); }
}

function bindWorkspaceEvents() {
  // Rail footer is re-rendered each context load; use delegation so the
  // context-modal and backfill buttons keep working after re-render.
  const railFooter = document.querySelector(".rail-footer");
  if (railFooter && !railFooter.dataset.bound) {
    railFooter.dataset.bound = "1";
    railFooter.addEventListener("click", (event) => {
      if (event.target.closest("#show-context")) {
        const modal = document.querySelector("#state-modal");
        if (modal) { modal.hidden = false; modal.style.display = "grid"; document.body.style.overflow = "hidden"; }
        return;
      }
      if (event.target.closest(".backfill-chapter")) {
        handleBackfillClick();
      }
    });
  }
  document.querySelectorAll(".scene-item[data-scene]").forEach((button) => button.addEventListener("click", () => {
    activeScene = button.dataset.scene;
    renderWorkspace();
  }));
  document.querySelectorAll(".beat-head").forEach((button) => button.addEventListener("click", () => {
    const body = button.parentElement.querySelector(".beat-body");
    const hidden = body.hasAttribute("hidden");
    body.toggleAttribute("hidden", !hidden);
    button.setAttribute("aria-expanded", String(hidden));
    button.lastElementChild.textContent = hidden ? "收起 ▴" : "展开 ▾";
  }));
  // Phase 6: generate prose for the current scene (real API), beat by beat with live progress
  document.querySelectorAll(".scene-generate").forEach((button) => button.addEventListener("click", async () => {
    const book = currentBook();
    const sceneId = currentWorkspaceContext && currentWorkspaceContext.scenes.find((s) => s.id === activeScene) ? activeScene : (currentWorkspaceContext && currentWorkspaceContext.scenes[0] ? currentWorkspaceContext.scenes[0].id : null);
    if (!apiAvailable || !book || !currentActiveChapterId || !sceneId) { toast("需要激活章节与场景后才能生成正文。"); return; }
    const scene = (currentWorkspaceContext?.scenes || []).find((s) => s.id === sceneId);
    const beats = (scene && scene.beats) || [];
    const pending = beats.filter((b) => b.status !== "applied" && b.status !== "completed");
    if (!beats.length) { toast("该场景尚无 Beat，请先生成节拍计划。"); return; }
    if (!pending.length) { toast("该场景全部 Beat 已完成。"); return; }
    let produced = 0;
    try {
      for (let i = 0; i < beats.length; i += 1) {
        const beat = beats[i];
        if (beat.status === "applied" || beat.status === "completed") continue;
        showThinking("正在生成 Scene 正文…", `Scene ${scene.title || "未命名"} · Beat ${beat.ordinal} / ${beats.length}：${beat.name || "未命名 Beat"}`);
        setThinkingProgress(produced, pending.length, `已应用 ${produced} / ${pending.length} 段 · 当前：Beat ${beat.ordinal} / ${beats.length}`);
        await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${sceneId}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_beat", beat_id: beat.id }), timeoutMs: 600000 });
        produced += 1;
      }
      setThinkingProgress(null);
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      renderWorkspace();
      toast(`当前 Scene 正文已生成并自动应用（${produced} 段）。`);
    } catch (error) {
      setThinkingProgress(null);
      generationFailToast(error, "正文生成失败，原文未被修改。");
    }
    finally { hideThinking(); }
  }));
  // Phase 6: generate prose for a single beat (auto-applied)
  document.querySelectorAll(".generate-beat").forEach((button) => button.addEventListener("click", async () => {
    const book = currentBook();
    const sceneId = button.dataset.sceneId;
    const beatId = button.dataset.beatId;
    const beatName = button.dataset.beatName || "当前 Beat";
    if (!apiAvailable || !book || !currentActiveChapterId || !sceneId || !beatId) { toast("需要激活章节与场景。"); return; }
    showThinking("正在生成 Beat 正文…", `${beatName} · AI 基于节拍指令写作`);
    try {
      await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${sceneId}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_beat", beat_id: beatId }), timeoutMs: 600000 });
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      renderWorkspace();
      toast("Beat 正文已生成并自动应用。");
    } catch (error) { generationFailToast(error, "正文生成失败。"); }
    finally { hideThinking(); }
  }));
  // Phase 6: regenerate an applied beat (creates a new applied version)
  document.querySelectorAll(".regenerate-beat").forEach((button) => button.addEventListener("click", async () => {
    const book = currentBook();
    const sceneId = button.dataset.sceneId;
    const beatId = button.dataset.beatId;
    if (!apiAvailable || !book || !currentActiveChapterId) { toast("需要激活章节。"); return; }
    showThinking("正在重新生成 Beat 正文…", "将创建新版本并自动应用，历史保留");
    try {
      await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${sceneId}/generations`, { method: "POST", body: JSON.stringify({ action: "regenerate_beat", beat_id: beatId }), timeoutMs: 600000 });
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`);
      renderWorkspace();
      toast("已生成新版本并自动应用，历史正文保留。");
    } catch (error) { generationFailToast(error, "重新生成失败。"); }
    finally { hideThinking(); }
  }));
  // Workspace Markdown editing: author can edit the candidate/current prose and apply it.
  document.querySelectorAll(".edit-beat").forEach((button) => button.addEventListener("click", () => {
    const card = button.closest(".beat-card");
    const body = card.querySelector(".beat-body");
    if (!body) return;
    const currentText = body.textContent.replace(/\s*收起 ▴\s*$/, "").trim();
    body.innerHTML = "";
    body.classList.add("editing");
    const ta = document.createElement("textarea");
    ta.className = "prose-editor";
    ta.rows = 9;
    ta.value = currentText;
    body.appendChild(ta);
    const actionsEl = card.querySelector(".beat-actions");
    actionsEl.innerHTML = `<button class="primary-button save-beat-prose" type="button" data-scene-id="${button.dataset.sceneId}" data-beat-id="${button.dataset.beatId}">保存并应用 →</button> <button class="secondary-button cancel-beat-edit" type="button">取消</button>`;
    const saveBtn = actionsEl.querySelector(".save-beat-prose");
    const cancelBtn = actionsEl.querySelector(".cancel-beat-edit");
    cancelBtn.addEventListener("click", () => { currentWorkspaceContext && renderWorkspace(); });
    saveBtn.addEventListener("click", async () => {
      const book = currentBook();
      const sceneId = saveBtn.dataset.sceneId;
      const beatId = saveBtn.dataset.beatId;
      const markdown = ta.value.trim();
      if (!apiAvailable || !book || !currentActiveChapterId || !sceneId || !beatId) { toast("需要激活章节。"); return; }
      if (!markdown) { toast("正文不能为空。"); return; }
      const beat = ((currentWorkspaceContext?.scenes || []).find((s) => s.id === sceneId)?.beats || []).find((b) => b.id === beatId);
      if (!beat) { toast("未找到该 Beat，请刷新。"); return; }
      try {
        await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${sceneId}/beats/${beatId}/prose-versions`, {
          method: "POST",
          body: JSON.stringify({ markdown, applied_by: "author", expected_version: beat.version }),
          timeoutMs: 60000,
        });
        currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
        renderWorkspace();
        toast("正文已由作者应用为 v" + (beat.version + 1) + "，历史版本保留。");
      } catch (error) {
        toast("应用失败：正文版本可能已变化，请刷新后重试。");
      }
    });
  }));
  // Phase 6: complete the rest of the chapter (beat by beat with live progress)
  // (backfill-chapter click is handled via rail-footer delegation -> handleBackfillClick)
  document.querySelectorAll(".generate-chapter-remaining").forEach((button) => button.addEventListener("click", async () => {
    const book = currentBook();
    if (!apiAvailable || !book || !currentActiveChapterId) { toast("需要激活章节。"); return; }
    showThinking("正在完成本章剩余正文…", "按 Scene / Beat 顺序逐段生成并自动应用");
    let produced = 0;
    try {
      // Enumerate scenes & beats from the latest context.
      let context = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      const scenes = context.scenes || [];
      const allBeats = [];
      scenes.forEach((scene) => (scene.beats || []).forEach((beat) => allBeats.push({ scene, beat })));
      const pending = allBeats.filter(({ beat }) => beat.status !== "applied" && beat.status !== "completed");
      if (!allBeats.length) { toast("本章尚无 Beat，请先生成场景与节拍计划。"); return; }
      for (let i = 0; i < allBeats.length; i += 1) {
        const { scene, beat } = allBeats[i];
        if (beat.status === "applied" || beat.status === "completed") continue;
        showThinking("正在生成章节剩余正文…", `Scene ${scene.ordinal} / ${scenes.length} · Beat ${beat.ordinal}：${beat.name || "未命名 Beat"}`);
        setThinkingProgress(produced, pending.length, `已应用 ${produced} / ${pending.length} 段 · 当前：Scene ${scene.ordinal} / ${scenes.length} · Beat ${beat.ordinal}`);
        await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${scene.id}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_beat", beat_id: beat.id }), timeoutMs: 600000 });
        produced += 1;
      }
      setThinkingProgress(null);
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      renderWorkspace();
      toast(`已生成并应用 ${produced} 段正文。`);
    } catch (error) { setThinkingProgress(null); generationFailToast(error, "本章剩余正文生成失败。"); }
    finally { hideThinking(); }
  }));
  // Phase 6: confirm chapter delta and activate next chapter
  document.querySelectorAll(".confirm-chapter-delta").forEach((button) => button.addEventListener("click", async () => {
    const book = currentBook();
    if (!apiAvailable || !book || !currentActiveChapterId) { toast("需要激活章节。"); return; }
    showThinking("正在确认 Chapter Delta…", "更新 Living State 并激活下一章");
    try {
      const result = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/deltas/confirm`, { method: "POST", body: JSON.stringify({}), timeoutMs: 300000 });
      if (result.next_chapter) {
        book.stage = "writing";
        currentActiveChapterId = result.next_chapter.id;
        currentWorkspaceContext = null;
        await loadWorkspaceContext();
        toast(`本章已完成，第 ${result.next_chapter.ordinal} 章已激活。`);
      } else {
        // Last chapter finished — the whole novel is complete. Show the settlement screen (step 6 reader).
        book.status = "completed";
        book.stage = "done";
        currentActiveChapterId = null;
        currentWorkspaceContext = null;
        showScreen("read");
        toast("🎉 全书已完成！进入阅读模式查看完整小说。");
      }
    } catch (error) {
      const detail = error && error.message;
      if (detail && detail.includes("Chapter 尚未全部完成")) {
        toast(detail);
      } else {
        generationFailToast(error, "Delta 确认失败。");
      }
    }
    finally { hideThinking(); }
  }));
  // Phase 5: generate scene plan from API
  document.querySelector(".generate-scene-plan")?.addEventListener("click", async () => {
    const book = currentBook();
    if (!apiAvailable || !book || !currentActiveChapterId) { toast("需要激活章节后才能生成场景计划。"); return; }
    showThinking("正在根据章节目标生成场景计划…", "AI 正在规划 Scene 顺序与节拍");
    try {
      const result = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_scene_plan" }), timeoutMs: 300000 });
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`);
      renderWorkspace();
      toast(`已生成 ${result.scenes.length} 个场景计划。`);
    } catch (error) { toast("场景计划生成失败，章节计划未变。"); }
    finally { hideThinking(); }
  });
  // Phase 5: generate beat plan for a scene
  document.querySelectorAll(".generate-beat-plan").forEach((button) => button.addEventListener("click", async () => {
    const book = currentBook();
    const sceneId = button.dataset.sceneId;
    if (!apiAvailable || !book || !currentActiveChapterId || !sceneId) { toast("需要激活章节后才能生成节拍计划。"); return; }
    showThinking("正在根据场景目标生成节拍计划…", "AI 正在规划 Beat 顺序");
    try {
      await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${sceneId}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_beat_plan" }), timeoutMs: 300000 });
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`);
      renderWorkspace();
      toast("节拍计划已生成。");
    } catch (error) { toast("节拍计划生成失败。"); }
    finally { hideThinking(); }
  }));
}

function showThinking(message = "AI 正在思考…", sub = "正在装配上下文与模型参数") {
  document.querySelector("#thinking-text").textContent = message;
  document.querySelector("#thinking-sub").textContent = sub;
  setThinkingProgress(null);
  const overlay = document.querySelector("#thinking-overlay");
  overlay.hidden = false;
  overlay.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function setThinkingProgress(done, total, label) {
  const wrap = document.querySelector("#thinking-progress");
  if (!wrap) return;
  if (done === null || done === undefined || !total) {
    wrap.hidden = true;
    wrap.style.display = "none";
    return;
  }
  const pct = Math.max(0, Math.min(100, Math.round((done / total) * 100)));
  const bar = document.querySelector("#thinking-progress-bar");
  const text = document.querySelector("#thinking-progress-text");
  if (bar) bar.style.width = `${pct}%`;
  if (text) text.textContent = label || `${done} / ${total}`;
  wrap.hidden = false;
  wrap.style.display = "flex";
}

function hideThinking() {
  const overlay = document.querySelector("#thinking-overlay");
  overlay.hidden = true;
  overlay.style.display = "none";
  document.body.style.overflow = "";
}

function simulateGeneration(label, complete, sub = "正在装配上下文与模型参数") {
  showThinking(label, sub);
  document.querySelectorAll(".primary-button,.secondary-button").forEach((button) => { if (!button.disabled) button.dataset.wasDisabled = "false"; });
  setTimeout(() => {
    hideThinking();
    document.querySelector("#save-state").textContent = "● 已保存";
    complete();
  }, 1150);
}

let ideaSaveTimer = null;
let ideaSaveInFlight = false;
let ideaSaveDirty = false;

async function flushIdeaSave(book) {
  if (!book || !apiAvailable || book.stage !== "idea") return;
  if (ideaSaveInFlight) {
    ideaSaveDirty = true;
    return;
  }
  ideaSaveInFlight = true;
  ideaSaveDirty = false;
  try {
    const updated = await apiRequest(`/stories/${book.id}/idea`, {
      method: "PUT",
      body: JSON.stringify({ idea_text: book.idea, expected_version: book.version || 1 }),
    });
    book.version = updated.version;
  } catch (error) {
    if (error && error.message === "API 409") {
      try {
        const fresh = await apiRequest(`/works/${book.id}`);
        book.version = fresh.version;
        if (book.stage === "idea" && fresh.stage === "idea") {
          const updated = await apiRequest(`/stories/${book.id}/idea`, {
            method: "PUT",
            body: JSON.stringify({ idea_text: book.idea, expected_version: fresh.version }),
          });
          book.version = updated.version;
        } else {
          book.stage = fresh.stage;
          renderIdea();
        }
      } catch (e) { /* 保留原文，不覆盖 */ }
    }
  } finally {
    ideaSaveInFlight = false;
    if (ideaSaveDirty) {
      clearTimeout(ideaSaveTimer);
      ideaSaveTimer = setTimeout(() => flushIdeaSave(currentBook()), 600);
    }
  }
}

async function generateConcept(book) {
  if (!book) return;
  if (apiAvailable) {
    if (!book.idea || !book.idea.trim()) { toast("请先写下创作意图，再生成概念。"); return; }
    await flushIdeaSave(book);
    showThinking("正在生成 Story Concept…", "AI 正在根据你的创意构建概念候选");
    try {
      const result = await apiRequest(`/stories/${book.id}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_concept" }), timeoutMs: 300000 });
      book.stage = "idea_locked";
      book.version = (book.version || 1) + 1;
      window.currentConceptVersion = result.artifact.version;
      applyConceptPayload(result.artifact.payload);
      const version = document.querySelector("#concept-version");
      if (version) version.textContent = `AI 候选 · v${result.artifact.version}`;
      showScreen("concept");
      toast("Story Concept 候选已生成。请编辑、锁定关键设定后确认。");
    } catch (error) { toast(error && error.message === "请求超时" ? "概念生成请求超时（模型较慢），后台可能仍在生成，请稍后刷新查看结果。" : "Concept 生成失败，原始创意未被修改。"); }
    finally { hideThinking(); }
    return;
  }
  book.stage = "concept";
  simulateGeneration("正在生成 Story Concept…", () => { showScreen("concept"); toast("Story Concept 候选已生成。请编辑、锁定关键设定后确认。"); });
}

function bindEvents() {
  document.querySelectorAll("[data-nav]").forEach((button) => button.addEventListener("click", () => {
    const nav = button.dataset.nav;
    if (nav === "works") { showScreen("works"); return; }
    if (!canAccessScreen(nav)) { toast(lockHintFor(nav)); return; }
    if (nav === "workspace") currentActiveChapterId = null; // stepbar always targets the active chapter
    showScreen(nav);
  }));
  document.querySelector("#reader-toc-list").addEventListener("click", (event) => {
    // Scene anchors take priority: they are nested inside chapter buttons.
    const sceneEl = event.target.closest("[data-read-scene]");
    if (sceneEl) {
      const [chapterId, sceneId] = sceneEl.dataset.readScene.split("|");
      readerScrollToScene(chapterId, sceneId);
      return;
    }
    const chapterBtn = event.target.closest("[data-read-chapter]");
    if (chapterBtn) {
      const chapter = (readerData.chapters || []).find((c) => c.id === chapterBtn.dataset.readChapter);
      if (chapter) renderReaderChapter(chapter);
    }
  });
  // Phase 8: paper book — page turn, toc, settings, click & keyboard
  document.querySelector("#book-next").addEventListener("click", () => bookTurnNext());
  document.querySelector("#book-prev").addEventListener("click", () => bookTurnPrev());
  document.querySelector("#paper-book").addEventListener("click", (event) => {
    if (event.target.closest(".book-page-right")) bookTurnNext();
    else if (event.target.closest(".book-page-left")) bookTurnPrev();
  });
  document.querySelector("#book-toc-list").addEventListener("click", (event) => {
    const row = event.target.closest("[data-book-chapter]");
    if (row) bookJumpToChapter(row.dataset.bookChapter);
  });
  document.querySelector("#book-settings").addEventListener("click", (event) => {
    const btn = event.target.closest(".book-opt-group button");
    if (!btn) return;
    const group = btn.closest(".book-opt-group");
    const key = group.dataset.setting;
    bookSettings[key] = key === "fontSize" || key === "lineHeight" ? Number(btn.dataset.v) : btn.dataset.v;
    saveBookSettings();
    applyBookSettingsUi();
  });
  // 键盘左右翻页（仅实体书页激活时）
  document.addEventListener("keydown", (event) => {
    const bookScreen = document.querySelector("#book");
    if (!bookScreen || !bookScreen.classList.contains("active")) return;
    if (event.key === "ArrowRight") { event.preventDefault(); bookTurnNext(); }
    else if (event.key === "ArrowLeft") { event.preventDefault(); bookTurnPrev(); }
  });
  document.querySelectorAll("[data-toast]").forEach((button) => button.addEventListener("click", () => toast(button.dataset.toast)));
  document.querySelector("#idea-input").addEventListener("input", (event) => {
    document.querySelector("#idea-count").textContent = `${event.target.value.length} / 2,000`;
    const book = currentBook();
    if (!book) return;
    book.idea = event.target.value;
    if (apiAvailable && book.stage === "idea") {
      ideaSaveDirty = true;
      clearTimeout(ideaSaveTimer);
      ideaSaveTimer = setTimeout(() => flushIdeaSave(book), 600);
    }
  });
  document.querySelector("#generate-concept").addEventListener("click", () => generateConcept(currentBook()));
  document.querySelector("#re-generate-concept").addEventListener("click", () => generateConcept(currentBook()));
  document.querySelector("#confirm-concept").addEventListener("click", async () => {
    const book = currentBook();
    if (apiAvailable && book) {
      if (!window.currentConceptVersion) { toast("请先点击「AI生成概念」，生成候选后再确认。"); return; }
      showThinking("正在确认 Concept…", "保存候选并推进到蓝图阶段");
      try {
        await saveConceptCandidate();
        const confirmed = await apiRequest(`/stories/${book.id}/concept/confirm`, { method: "POST", body: JSON.stringify({ expected_version: window.currentConceptVersion }), timeoutMs: 300000 });
        window.currentConceptVersion = confirmed.version;
        window.currentConceptStatus = "confirmed";
        book.stage = "concept_confirmed";
        const renamed = await refreshStoryTitle(book);
        document.querySelector("#confirm-concept").style.display = "none";
        document.querySelector("#concept-stage-note").textContent = "已确认 · 当前版本为权威 Concept";
        // 确认后自动生成蓝图候选，无需用户再点「生成候选」
        showThinking("正在根据概念生成蓝图…", "AI 正在构建 Characters / World / Timeline / Arc");
        try {
          const result = await apiRequest(`/stories/${book.id}/blueprint/generations`, { method: "POST", body: JSON.stringify({ action: "generate_blueprint" }), timeoutMs: 300000 });
          result.artifacts.forEach((artifact) => { if (blueprintData[artifact.kind]) blueprintPayloadToUi(artifact.kind, artifact); });
          blueprintHasData = true;
          window.currentBlueprintVersions = Object.fromEntries(result.artifacts.map((artifact) => [artifact.kind, artifact.version]));
          toast(renamed ? `Concept 已确认，AI 已生成书名《${book.title}》，蓝图候选已自动生成。` : "Concept 已确认，蓝图候选已自动生成，请查看后确认。");
        } catch (blueprintError) {
          blueprintHasData = false;
          toast(renamed ? `Concept 已确认，AI 已生成书名《${book.title}》；蓝图自动生成失败，可稍后手动生成。` : "Concept 已确认；蓝图自动生成失败，可稍后手动生成。");
        }
        showScreen("blueprint");
      } catch (error) {
        const message = error && error.message === "请求超时" ? "确认请求超时（模型较慢），后台可能仍在处理，请稍后刷新查看结果。" : "Concept 确认失败，请检查版本是否已更新。";
        toast(message);
      }
      finally { hideThinking(); }
      return;
    }
    simulateGeneration("正在保存 Concept 并生成 Blueprint…", () => { showScreen("blueprint"); toast("Concept 已确认。Blueprint 保持为候选，需再次确认后创建章节计划。"); });
  });
  document.querySelector("#generate-blueprint").addEventListener("click", async () => {
    const book = currentBook();
    if (apiAvailable && book) {
      showThinking("正在生成四类蓝图候选…", "AI 正在构建 Characters / World / Timeline / Arc");
      try {
        const result = await apiRequest(`/stories/${book.id}/blueprint/generations`, { method: "POST", body: JSON.stringify({ action: "generate_blueprint" }), timeoutMs: 300000 });
        result.artifacts.forEach((artifact) => { if (blueprintData[artifact.kind]) blueprintPayloadToUi(artifact.kind, artifact); });
        blueprintHasData = true;
        window.currentBlueprintVersions = Object.fromEntries(result.artifacts.map((artifact) => [artifact.kind, artifact.version]));
        document.querySelector("#blueprint-stage-note").textContent = "AI 候选 · 尚未确认";
        renderBlueprint("characters");
        toast("Blueprint 四个分类候选已生成，请逐项查看后确认。");
      } catch (error) { toast("Blueprint 生成失败，请先确认 Concept。"); }
      finally { hideThinking(); }
      return;
    }
    toast("当前为本地原型演示，蓝图候选使用示例数据。");
  });
  document.querySelector("#confirm-blueprint").addEventListener("click", async () => {
    const book = currentBook();
    if (apiAvailable && book && window.currentBlueprintVersions) {
      showThinking("正在确认 Blueprint…", "更新作品阶段并创建初始 Living State");
      try {
        await apiRequest(`/stories/${book.id}/blueprint/confirm`, { method: "POST", body: JSON.stringify({ expected_versions: window.currentBlueprintVersions }) });
        book.stage = "blueprint_confirmed";
        document.querySelector("#confirm-blueprint").style.display = "none";
        document.querySelector("#blueprint-stage-note").textContent = "已确认 · 当前版本为权威 Blueprint";
        const toChapters = document.querySelector("#to-chapters");
        if (toChapters) toChapters.style.display = "";
        // 确认后自动生成章节雏形，无需用户再点「生成章节雏形」
        showThinking("正在根据蓝图规划章节…", "AI 正在生成章节卡片与逐章激活");
        try {
          const result = await apiRequest(`/stories/${book.id}/chapter-plan`, { method: "POST", body: JSON.stringify({ action: "generate_chapter_plan" }), timeoutMs: 300000 });
          book.stage = "chapter_planning";
          window.currentChapters = result.chapters;
          renderChaptersFromApi(result.chapters);
          document.querySelector("#chapter-plan-note").textContent = "已生成 · 第 1 章已激活";
          toast("Blueprint 已确认，章节雏形已自动生成。仅第 1 章可进入工作台。");
        } catch (chapterError) {
          window.currentChapters = [];
          document.querySelector("#chapter-plan-note").textContent = "蓝图已确认 · 可生成章节雏形";
          toast("Blueprint 已确认；章节自动生成失败，可稍后手动生成。");
        }
        showScreen("chapters");
      } catch (error) { toast("Blueprint 确认失败，请确保四个分类都已生成且版本未冲突。"); }
      finally { hideThinking(); }
      return;
    }
    simulateGeneration("正在生成 Chapter Plan 雏形…", () => { showScreen("chapters"); toast("章节雏形已生成。仅 Chapter 01 处于 active 状态。"); });
  });
  document.querySelector("#to-chapters").addEventListener("click", () => showScreen("chapters"));
  document.querySelector("#open-workspace").addEventListener("click", () => {
    currentActiveChapterId = null; // always open the active chapter from the chapter-plan page
    showScreen("workspace");
  });
  document.querySelector("#generate-chapter-plan").addEventListener("click", async () => {
    const book = currentBook();
    if (!apiAvailable || !book) { toast("当前没有可生成的作品。"); return; }
    showThinking("正在根据蓝图规划章节…", "AI 正在生成章节卡片与逐章激活");
    try {
      const result = await apiRequest(`/stories/${book.id}/chapter-plan`, { method: "POST", body: JSON.stringify({ action: "generate_chapter_plan" }), timeoutMs: 300000 });
      book.stage = "chapter_planning";
      window.currentChapters = result.chapters;
      renderChaptersFromApi(result.chapters);
      document.querySelector("#chapter-plan-note").textContent = "已生成 · 第 1 章已激活";
      toast("章节雏形已生成。仅第 1 章可进入工作台。");
    } catch (error) { toast("章节计划生成失败，请先确认 Blueprint。"); }
    finally { hideThinking(); }
  });
  document.querySelectorAll(".blueprint-tab").forEach((tab) => tab.addEventListener("click", () => renderBlueprint(tab.dataset.blueprint)));
  document.querySelector("#chapter-grid").addEventListener("click", (event) => {
    const target = event.target.closest("[data-nav], [data-chapter-id]");
    if (!target) return;
    if (target.dataset.nav) { showScreen(target.dataset.nav); return; }
    if (target.dataset.chapterId) {
      // Open a completed chapter in the workspace (read-only review).
      currentActiveChapterId = target.dataset.chapterId;
      showScreen("workspace");
    }
  });
  const modal = document.querySelector("#state-modal");
  const openModal = () => { modal.hidden = false; modal.style.display = "grid"; document.body.style.overflow = "hidden"; };
  const closeModal = () => { modal.hidden = true; modal.style.display = "none"; document.body.style.overflow = ""; };
  document.querySelector("#open-state").addEventListener("click", openModal);
  document.querySelector("#open-state-full").addEventListener("click", openModal);
  document.querySelectorAll(".modal-close").forEach((button) => button.addEventListener("click", closeModal));
  modal.addEventListener("click", (event) => { if (event.target === modal) closeModal(); });
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-config]")) openConfig();
    if (event.target.closest("[data-title-edit]")) openTitleModal();
  });
  document.querySelector("#save-title").addEventListener("click", saveTitle);
  document.querySelector("#title-input").addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); saveTitle(); } });
  document.querySelectorAll("[data-close-title]").forEach((button) => button.addEventListener("click", () => hideModal("#title-modal")));
  document.querySelector("#config-temp").addEventListener("input", (event) => {
    document.querySelector("#config-temp-value").textContent = event.target.value;
  });
  document.querySelector("#save-config").addEventListener("click", () => {
    aiConfig.model = document.querySelector("#config-model").value;
    aiConfig.temperature = Number(document.querySelector("#config-temp").value);
    aiConfig.reasoning = document.querySelector("#config-reasoning").value;
    const book = currentBook();
    const payload = { model: aiConfig.model, temperature: aiConfig.temperature, reasoning_strength: aiConfig.reasoning, expected_version: aiConfig.version || 1 };
    const saved = apiAvailable && book ? apiRequest(`/stories/${book.id}/ai-config`, { method: "PUT", body: JSON.stringify(payload) }) : Promise.resolve();
    saved.then((config) => { if (config) aiConfig.version = config.version; }).catch(() => undefined).finally(() => hideModal("#config-modal"));
    const level = aiConfig.reasoning === "high" ? "高" : aiConfig.reasoning === "low" ? "低" : "中";
    toast(`生成设置已保存：${aiConfig.model} · temp ${aiConfig.temperature} · 推理强度 ${level}`);
  });
  document.querySelectorAll("[data-close-config]").forEach((button) => button.addEventListener("click", () => hideModal("#config-modal")));
  document.querySelector("#show-write-tips").addEventListener("click", () => showModal("#tips-modal"));
  document.querySelectorAll("[data-close-tips]").forEach((button) => button.addEventListener("click", () => hideModal("#tips-modal")));
  document.querySelector("#complete-chapter").addEventListener("click", async () => {
    const book = currentBook();
    if (!apiAvailable || !book || !currentActiveChapterId) { toast("需要激活章节后才能生成。"); return; }
    let totalProduced = 0;
    try {
      // 1. Ensure a scene plan exists (with progress feedback).
      let context = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      if (!context.scenes.length) {
        showThinking("正在一键生成整个章节…", "第 1 步 / 4：生成场景计划");
        await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_scene_plan" }), timeoutMs: 300000 });
        context = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      }
      // 2. Scene by scene: ensure beat plan, then generate each beat's prose (auto-applied).
      const scenes = context.scenes || [];
      for (let s = 0; s < scenes.length; s += 1) {
        const scene = scenes[s];
        if (!scene.beats || !scene.beats.length) {
          showThinking("正在一键生成整个章节…", `第 2 步 / 4 · Scene ${s + 1} / ${scenes.length}：生成节拍计划`);
          await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${scene.id}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_beat_plan" }), timeoutMs: 300000 });
          context = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
        }
        const freshScene = (context.scenes || []).find((x) => x.id === scene.id) || scene;
        const beats = freshScene.beats || [];
        const pendingInScene = beats.filter((b) => b.status !== "applied" && b.status !== "completed");
        for (let b = 0; b < beats.length; b += 1) {
          const beat = beats[b];
          if (beat.status === "applied" || beat.status === "completed") continue;
          showThinking("正在一键生成整个章节…", `Scene ${s + 1} / ${scenes.length} · Beat ${b + 1} / ${beats.length}：${beat.name || "未命名 Beat"}`);
          setThinkingProgress(b, beats.length, `Scene ${s + 1} / ${scenes.length} · 已应用 ${b} / ${beats.length} 段`);
          await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/scenes/${scene.id}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_beat", beat_id: beat.id }), timeoutMs: 600000 });
          totalProduced += 1;
        }
        setThinkingProgress(null);
      }
      currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
      renderWorkspace();
      toast(totalProduced ? `一键生成完成：已生成并应用 ${totalProduced} 段正文。请确认 Chapter Delta 后进入下一章。` : "本章正文已全部生成并应用，请确认 Chapter Delta 后进入下一章。");
    } catch (error) {
      // A step may have timed out on the client while the server finished; refresh to show the real state.
      setThinkingProgress(null);
      try {
        currentWorkspaceContext = await apiRequest(`/stories/${book.id}/chapters/${currentActiveChapterId}/context`, { timeoutMs: 60000 });
        renderWorkspace();
      } catch (e) { /* keep previous render */ }
      toast("一键生成遇到超时或失败，已刷新显示实际已生成内容，可再次点击继续。");
    }
    finally { hideThinking(); }
  });
  document.querySelector("#show-context").addEventListener("click", openModal);
  document.querySelector("#add-model").addEventListener("click", () => toast("配置表单将以服务端环境变量引用 API Key；原型不接收或展示真实密钥。"));
  document.querySelector("#save-models").addEventListener("click", () => { toast("模型路由策略已保存（模拟）。后续生成可在页面级下拉菜单临时覆盖。" ); });
  document.querySelector("#book-grid").addEventListener("click", (event) => {
    const open = event.target.closest("[data-open]");
    if (open) {
      activeBook = open.dataset.open;
      // 切换故事时重置上一故事的章节/工作台/阅读状态，避免残留章节 ID 请求到新故事（404）
      currentActiveChapterId = null;
      currentWorkspaceContext = null;
      readerData = null;
      readerActiveChapter = null;
      window.currentBlueprintVersions = {};
      blueprintHasData = false;
      const book = books.find((b) => b.id === activeBook);
      // Completed works open directly into the reading mode (step 6).
      if (book && book.stage === "done") {
        showScreen("read");
      } else {
        showScreen("idea");
      }
      // 进入故事时以后端为准刷新真实 stage，并据此锁定未解锁的步骤。
      refreshBookStage(book);
      return;
    }
    const del = event.target.closest(".delete-book");
    if (del) openDelete(del.dataset.id);
  });
  document.querySelector("#blueprint-content").addEventListener("click", (event) => {
    const link = event.target.closest(".history-link");
    if (link) {
      const [kind, index] = link.dataset.history.split("|");
      openHistory(kind, Number(index));
    }
  });
  document.addEventListener("click", (event) => {
    if (event.target.closest("#new-book")) createNewBook();
  });
  document.querySelectorAll("[data-close-history]").forEach((button) => button.addEventListener("click", () => hideModal("#history-modal")));
  document.querySelectorAll("[data-close-confirm]").forEach((button) => button.addEventListener("click", closeDelete));
  document.querySelector("#confirm-delete").addEventListener("click", async () => {
    const index = books.findIndex((book) => book.id === pendingDeleteId);
    if (index > -1) {
      const name = books[index].title;
      if (apiAvailable) {
        try {
          await apiRequest(`/works/${pendingDeleteId}`, { method: "DELETE" });
        } catch (error) {
          toast("删除失败，作品仍然保留。");
          closeDelete();
          return;
        }
      }
      books.splice(index, 1);
      if (activeBook === pendingDeleteId) {
        activeBook = null;
        renderBooks();
        showScreen("works");
      } else {
        renderBooks();
      }
      toast(`已删除《${name}》。`);
    }
    closeDelete();
  });
}

let modelPromptProfiles = [];

async function loadModelPromptProfiles() {
  try {
    modelPromptProfiles = await apiRequest("/models/prompt-profiles", { timeoutMs: 10000 });
  } catch (error) {
    modelPromptProfiles = [];
  }
  renderModels();
}

function renderModels() {
  const availability = Object.fromEntries((modelAvailability || []).map((m) => [m.provider, m]));
  const models = [
    ["deepseek", "DeepSeek V4 Flash", "适合快速结构化规划与正文生成", "https://api.deepseek.com"],
    ["agnes", "Agnes 2.5 Flash", "适合结构化候选与一致性检查", "https://apihub.agnes-ai.com"],
    ["grok", "Grok 4.5", "适合高探索性候选与复杂推理", "https://modelflare.dev"],
    ["ollama", "Qwen3.6 Abliterated 27B (Ollama)", "远端 Ollama · 推理默认开启，适合高探索性创作", "http://106.75.216.144:11434"],
  ];
  const profiles = Object.fromEntries((modelPromptProfiles || []).map((p) => [p.provider, p]));
  document.querySelector("#model-cards").innerHTML = models.map(([provider, name, description, endpoint]) => {
    const profile = profiles[provider] || { system_prompt: "", version: 0 };
    const state = availability[provider];
    const online = !state || state.available;
    const stateText = online ? "可用" : "离线 · 不可用";
    return `<article class="model-card"><div><h3>${name} <span class="tag ${online ? "green" : "amber"}">${stateText}</span></h3><p>${description}</p><small>${endpoint} · API Key 仅由服务端持有</small></div><label class="form-field" style="margin-top:12px"><span>模型预设系统提示词 <small>与每项任务提示词叠加，不覆盖任务目标、格式与边界</small></span><textarea class="model-prompt-input" data-provider="${provider}" maxlength="12000" rows="5" placeholder="例如：使用大众易懂的中文；优先清晰因果与自然过渡；保持克制而具体的叙述。">${escapeHtml(profile.system_prompt || "")}</textarea></label><div class="model-card-actions"><span class="tag">预设 v${profile.version || 0}</span><button class="secondary-button save-model-prompt" type="button" data-provider="${provider}" data-version="${profile.version || 0}">保存预设</button></div></article>`;
  }).join("");
  document.querySelectorAll(".save-model-prompt").forEach((button) => button.addEventListener("click", async () => {
    const provider = button.dataset.provider;
    const input = document.querySelector(`.model-prompt-input[data-provider="${provider}"]`);
    if (!input) return;
    button.disabled = true;
    try {
      await apiRequest(`/models/${provider}/prompt-profile`, { method: "PUT", body: JSON.stringify({ system_prompt: input.value, expected_version: Number(button.dataset.version || 0) }) });
      toast("模型预设系统提示词已持久化保存。任务提示词会与其叠加，不会被覆盖。");
      await loadModelPromptProfiles();
    } catch (error) {
      generationFailToast(error, "保存失败：配置可能已被其他页面更新，请刷新后重试。");
    } finally {
      button.disabled = false;
    }
  }));
}

async function bootstrap() {
  await loadWorksFromApi();
  loadModelAvailability(); // 异步探测模型可用性（Ollama 远程服务器可能离线），不可用模型会置为禁用
  renderBlueprint();
  renderBooks();
  renderChapters();
  renderWorkspace();
  renderModels();
  loadModelPromptProfiles();
  renderIdea();
  updateTopState();
  loadBookSettings();
  bindEvents();
}

bootstrap();
