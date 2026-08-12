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
const API_BASE = "/api/v1";
let apiAvailable = false;

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.status === 204 ? null : response.json();
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
    document.querySelector("#concept-stage-note").textContent = artifact.status === "confirmed" ? "已确认 · 当前版本为权威 Concept" : "AI 候选 · 尚未确认";
    const confirm = document.querySelector("#confirm-concept");
    if (confirm) confirm.style.display = artifact.status === "confirmed" ? "none" : "";
  } catch (error) {
    window.currentConceptVersion = 0;
  }
}

function blueprintPayloadToUi(kind, artifact) {
  if (!artifact?.payload) return;
  const entry = artifact.payload.entries?.[0];
  if (!entry) return;
  const fields = entry.fields || {};
  blueprintData[kind].entries = [{
    name: entry.name || kind,
    role: entry.role || "全局设定",
    version: artifact.version,
    updated: artifact.updated_at?.slice(0, 10) || "刚刚",
    lock: artifact.locked_paths?.length ? "部分字段已锁定" : "",
    fields: Object.entries(fields).map(([label, value]) => [label, Array.isArray(value) ? value.join("；") : String(value)]),
    history: [{ version: `v${artifact.version}`, date: artifact.updated_at?.slice(0, 10) || "刚刚", by: artifact.status === "confirmed" ? "作者确认" : "AI 候选", note: "来自真实 Blueprint API", detail: "当前版本从后端 Story Artifact 读取。" }],
  }];
}

async function loadBlueprintForCurrentStory() {
  const book = currentBook();
  if (!apiAvailable || !book) return;
  try {
    const data = await apiRequest(`/stories/${book.id}/blueprint`);
    const hasAny = ["characters", "world", "timeline", "arc"].some((kind) => data[kind]);
    blueprintHasData = hasAny;
    window.currentBlueprintVersions = {};
    if (hasAny) {
      Object.entries(data).forEach(([kind, artifact]) => { if (artifact && blueprintData[kind]) blueprintPayloadToUi(kind, artifact); });
      ["characters", "world", "timeline", "arc"].forEach((kind) => { if (data[kind]) window.currentBlueprintVersions[kind] = data[kind].version; });
    }
    const confirmed = ["characters", "world", "timeline", "arc"].every((kind) => data[kind]?.status === "confirmed");
    document.querySelector("#confirm-blueprint").style.display = confirmed ? "none" : "";
    document.querySelector("#blueprint-stage-note").textContent = confirmed ? "已确认 · 当前版本为权威 Blueprint" : (hasAny ? "AI 候选 · 尚未确认" : "尚未生成");
    renderBlueprint(document.querySelector(".blueprint-tab.active")?.dataset.blueprint || "characters");
  } catch (error) {
    window.currentBlueprintVersions = {};
  }
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
  document.querySelectorAll(".screen").forEach((screen) => screen.classList.toggle("active", screen.id === id));
  document.querySelectorAll("[data-nav]").forEach((button) => button.classList.toggle("active", button.dataset.nav === id));
  if (id === "workspace") renderWorkspace();
  if (id === "works") renderBooks();
  if (id === "idea") renderIdea();
  if (id === "concept") loadConceptForCurrentStory();
  if (id === "blueprint") loadBlueprintForCurrentStory();
  if (id === "chapters") loadChaptersForCurrentStory();
  updateTopState();
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
  if (!blueprintHasData && currentBook()) {
    renderBlueprintEmpty();
    return;
  }
  const entry = blueprintData[kind];
  const cards = entry.entries.map((item, index) => `
    <article class="bp-entry">
      <div class="bp-entry-head">
        <div><h3>${item.name}</h3><span class="bp-role">${item.role}</span></div>
        <div class="bp-entry-tags">${item.lock ? `<span class="tag amber">🔒 ${item.lock}</span>` : ""}<span class="tag blue">v${item.version} · 更新于 ${item.updated}</span></div>
      </div>
      <div class="bp-fields">${item.fields.map(([label, value]) => `<div class="bp-field"><span>${label}</span><p>${value}</p></div>`).join("")}</div>
      <div class="bp-entry-foot"><button class="text-button history-link" type="button" data-history="${kind}|${index}">查看更新履历（${item.history.length} 条）</button></div>
    </article>`).join("");
  document.querySelector("#blueprint-content").innerHTML = `
    <section class="content-panel panel">
      <div class="content-head"><div><h2>${entry.title}</h2><p>${entry.description}</p></div><button class="secondary-button" type="button" data-toast="此处展示的是可编辑的原型结构；锁定字段需要作者显式解除后才能修改。">编辑设定</button></div>
      <div class="bp-entries">${cards}</div>
      <div class="living-banner"><b>状态更新边界：</b> Beat / Scene 只生成 proposed 候选；仅 Chapter Delta 经作者确认后更新 Living State，并作为下一章 Snapshot 的新增事实。</div>
    </section>`;
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

function openHistory(kind, index) {
  const entry = blueprintData[kind].entries[index];
  document.querySelector("#history-title").textContent = `更新履历 · ${entry.name}`;
  document.querySelector("#history-subtitle").textContent = `${blueprintData[kind].title} · 当前为最新版本 v${entry.version}`;
  document.querySelector("#history-list").innerHTML = entry.history.map((item) => `
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
  if (apiAvailable && book) apiRequest(`/stories/${book.id}/ai-config`).then(apply).catch(() => apply(aiConfig));
  else apply(aiConfig);
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
  document.querySelector("#chapter-grid").innerHTML = items.map((chapter) => {
    const active = chapter.access_status === "active";
    return `<article class="chapter-card ${active ? "active" : "locked"}">
      <span class="chapter-number">CHAPTER ${String(chapter.ordinal).padStart(2, "0")}</span>
      <span class="tag ${active ? "blue" : ""}">${active ? "可进入 · 当前章" : "🔒 未激活 · 雏形"}</span>
      <h3>${chapter.title}</h3><p>${chapter.goal || chapter.summary}</p>
      <button class="${active ? "primary-button" : "secondary-button"}" type="button" ${active ? "data-nav=\"workspace\"" : "data-toast=\"后序章节保持锁定，完成当前章并确认 Chapter Delta 后才会激活。\""}>${active ? "进入工作台 →" : "查看计划雏形"}</button>
    </article>`;
  }).join("");
  const active = items.find((chapter) => chapter.access_status === "active");
  if (active) document.querySelector(".chapter-summary").firstElementChild.innerHTML = `<b>${items.length} 章</b><span>·</span>当前计划 · 第 ${active.ordinal} 章已激活`;
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

function renderWorkspace() {
  document.querySelector("#scene-items").innerHTML = scenes.map((scene) => `<button class="scene-item ${scene.status} ${scene.id === activeScene ? "current" : ""}" type="button" data-scene="${scene.id}" ${scene.status === "locked" ? "disabled" : ""}>${scene.status === "done" ? "✓ " : ""}Scene ${scene.id} · ${scene.name}<small>${scene.hint}</small></button>`).join("");
  const data = sceneContent[activeScene];
  document.querySelector("#active-scene-label").textContent = data.title;
  document.querySelector("#editor-status").textContent = activeScene === 2 ? "当前 Scene" : activeScene === 1 ? "已完成" : "计划中";
  document.querySelector("#scene-content").innerHTML = `<div class="scene-title-row"><h2 class="scene-title">${data.title}</h2><button class="primary-button scene-generate" type="button">一键生成整个 Scene</button><button class="config-button" type="button" data-config>⚙ 生成设置</button></div><p class="scene-subtitle">${data.subtitle}</p><div class="scene-overview"><b>Scene 描述</b><br>${data.overview}</div>${data.beats.map(beatHtml).join("")}`;
  bindWorkspaceEvents();
}

function bindWorkspaceEvents() {
  document.querySelectorAll(".scene-item[data-scene]").forEach((button) => button.addEventListener("click", () => {
    activeScene = Number(button.dataset.scene);
    renderWorkspace();
  }));
  document.querySelectorAll(".beat-head").forEach((button) => button.addEventListener("click", () => {
    const body = button.parentElement.querySelector(".beat-body");
    const hidden = body.hasAttribute("hidden");
    body.toggleAttribute("hidden", !hidden);
    button.setAttribute("aria-expanded", String(hidden));
    button.lastElementChild.textContent = hidden ? "收起 ▴" : "展开 ▾";
  }));
  document.querySelector(".generate-beat")?.addEventListener("click", () => simulateGeneration("正在基于 Chapter 01 Snapshot 生成 Beat 正文…", () => {
    generatedBeat = true;
    document.querySelector("#delta-count").textContent = "3 条 · 待确认";
    renderWorkspace();
    toast("Beat 候选已生成。原文未被替换，应用后会创建新版本与候选 Delta。");
  }));
  document.querySelectorAll(".scene-generate").forEach((button) => button.addEventListener("click", () => {
    simulateGeneration(`正在按 Beat 顺序生成「${sceneContent[activeScene].title}」…`, () => {
      generatedBeat = true;
      renderWorkspace();
      toast("当前 Scene 的候选内容已生成。已完成 Beat 不会被覆盖。");
    });
  }));
}

function showThinking(message = "AI 正在思考…", sub = "正在装配上下文与模型参数") {
  document.querySelector("#thinking-text").textContent = message;
  document.querySelector("#thinking-sub").textContent = sub;
  const overlay = document.querySelector("#thinking-overlay");
  overlay.hidden = false;
  overlay.style.display = "flex";
  document.body.style.overflow = "hidden";
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

function bindEvents() {
  document.querySelectorAll("[data-nav]").forEach((button) => button.addEventListener("click", () => showScreen(button.dataset.nav)));
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
  document.querySelector("#generate-concept").addEventListener("click", async () => {
    const book = currentBook();
    if (apiAvailable && book) {
      if (!book.idea || !book.idea.trim()) { toast("请先写下创作意图，再生成概念。"); return; }
      await flushIdeaSave(book);
      showThinking("正在生成 Story Concept…", "AI 正在根据你的创意构建概念候选");
      try {
        const result = await apiRequest(`/stories/${book.id}/generations`, { method: "POST", body: JSON.stringify({ action: "generate_concept" }) });
        book.stage = "idea_locked";
        book.version = (book.version || 1) + 1;
        window.currentConceptVersion = result.artifact.version;
        applyConceptPayload(result.artifact.payload);
        showScreen("concept");
        toast("Story Concept 候选已生成。请编辑、锁定关键设定后确认。");
      } catch (error) { toast("Concept 生成失败，原始创意未被修改。"); }
      finally { hideThinking(); }
      return;
    }
    if (book) book.stage = "concept";
    simulateGeneration("正在生成 Story Concept…", () => { showScreen("concept"); toast("Story Concept 候选已生成。请编辑、锁定关键设定后确认。"); });
  });
  document.querySelector("#confirm-concept").addEventListener("click", async () => {
    const book = currentBook();
    if (apiAvailable && book) {
      if (!window.currentConceptVersion) { toast("请先点击「AI生成概念」，生成候选后再确认。"); return; }
      showThinking("正在确认 Concept…", "保存候选并推进到蓝图阶段");
      try {
        await saveConceptCandidate();
        const confirmed = await apiRequest(`/stories/${book.id}/concept/confirm`, { method: "POST", body: JSON.stringify({ expected_version: window.currentConceptVersion }) });
        window.currentConceptVersion = confirmed.version;
        window.currentConceptStatus = "confirmed";
        book.stage = "concept_confirmed";
        const renamed = await refreshStoryTitle(book);
        document.querySelector("#confirm-concept").style.display = "none";
        document.querySelector("#concept-stage-note").textContent = "已确认 · 当前版本为权威 Concept";
        toast(renamed ? `Concept 已确认，AI 已生成书名《${book.title}》，可点击顶部书名修改。` : "Concept 已确认，正在进入蓝图。");
        showScreen("blueprint");
      } catch (error) { toast("Concept 确认失败，请检查版本是否已更新。"); }
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
        const result = await apiRequest(`/stories/${book.id}/blueprint/generations`, { method: "POST", body: JSON.stringify({ action: "generate_blueprint" }) });
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
        toast("Blueprint 已确认，正在进入章节规划。");
        showScreen("chapters");
      } catch (error) { toast("Blueprint 确认失败，请确保四个分类都已生成且版本未冲突。"); }
      finally { hideThinking(); }
      return;
    }
    simulateGeneration("正在生成 Chapter Plan 雏形…", () => { showScreen("chapters"); toast("章节雏形已生成。仅 Chapter 01 处于 active 状态。"); });
  });
  document.querySelector("#open-workspace").addEventListener("click", () => showScreen("workspace"));
  document.querySelector("#generate-chapter-plan").addEventListener("click", async () => {
    const book = currentBook();
    if (!apiAvailable || !book) { toast("当前没有可生成的作品。"); return; }
    showThinking("正在根据蓝图规划章节…", "AI 正在生成章节卡片与逐章激活");
    try {
      const result = await apiRequest(`/stories/${book.id}/chapter-plan`, { method: "POST", body: JSON.stringify({ action: "generate_chapter_plan" }) });
      window.currentChapters = result.chapters;
      renderChaptersFromApi(result.chapters);
      document.querySelector("#chapter-plan-note").textContent = "已生成 · 第 1 章已激活";
      toast("章节雏形已生成。仅第 1 章可进入工作台。");
    } catch (error) { toast("章节计划生成失败，请先确认 Blueprint。"); }
    finally { hideThinking(); }
  });
  document.querySelectorAll(".blueprint-tab").forEach((tab) => tab.addEventListener("click", () => renderBlueprint(tab.dataset.blueprint)));
  document.querySelector("#chapter-grid").addEventListener("click", (event) => { const target = event.target.closest("[data-nav]"); if (target) showScreen(target.dataset.nav); });
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
  document.querySelector("#complete-chapter").addEventListener("click", () => simulateGeneration("正在从当前 Beat 顺序生成本章剩余内容…", () => {
    generatedBeat = true;
    renderWorkspace();
    toast("模拟执行已暂停在作者确认点：Chapter Delta 必须确认后，才能更新 Living State 并激活下一章。");
  }));
  document.querySelector("#show-context").addEventListener("click", openModal);
  document.querySelector("#add-model").addEventListener("click", () => toast("配置表单将以服务端环境变量引用 API Key；原型不接收或展示真实密钥。"));
  document.querySelector("#save-models").addEventListener("click", () => { toast("模型路由策略已保存（模拟）。后续生成可在页面级下拉菜单临时覆盖。" ); });
  document.querySelector("#book-grid").addEventListener("click", (event) => {
    const open = event.target.closest("[data-open]");
    if (open) {
      activeBook = open.dataset.open;
      showScreen("idea");
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

function renderModels() {
  const models = [
    ["DeepSeek V4 Flash", "OpenAI Chat Completions compatible · 适合快速结构化规划与正文生成", "https://api.deepseek.com", "运行正常 · 842ms"],
    ["Agnes 2.0 Flash", "OpenAI Chat Completions compatible · 适合结构化候选与一致性检查", "https://apihub.agnes-ai.com", "运行正常 · 713ms"],
    ["Grok 4.5", "OpenAI Chat Completions compatible · 用于高探索性候选；不要求结构化响应格式", "https://modelflare.dev", "尚未测试"]
  ];
  document.querySelector("#model-cards").innerHTML = models.map(([name, description, endpoint, status], index) => `<article class="model-card"><div><h3>${name} <span class="tag green">已启用</span></h3><p>${description}</p><small>${endpoint} · API Key: 服务端环境变量</small></div><div class="model-card-actions"><button class="secondary-button test-model" type="button" data-model="${name}" data-index="${index}">测试配置</button><button class="icon-button" type="button" aria-label="编辑 ${name}" data-toast="真实实现应编辑服务端模型配置，前端仅显示脱敏状态。">⚙</button></div><div class="test-result" data-result="${index}" ${index === 2 ? "hidden" : ""}>✓ ${status} · 返回结构化候选验证通过</div></article>`).join("");
  document.querySelectorAll(".test-model").forEach((button) => button.addEventListener("click", () => {
    button.disabled = true;
    button.textContent = "测试中…";
    setTimeout(() => {
      const result = document.querySelector(`[data-result="${button.dataset.index}"]`);
      result.hidden = false;
      result.textContent = "✓ 连接成功 · 786ms · 密钥与响应内容均未暴露到浏览器";
      button.disabled = false;
      button.textContent = "再次测试";
      toast(`${button.dataset.model} 配置测试成功。`);
    }, 950);
  }));
}

async function bootstrap() {
  await loadWorksFromApi();
  renderBlueprint();
  renderBooks();
  renderChapters();
  renderWorkspace();
  renderModels();
  renderIdea();
  updateTopState();
  bindEvents();
}

bootstrap();
