export const mockUser = {
  name: '聪明的一休',
  avatar: '/static/avatar-1.png',
  department: 'AI 原生项目协作组',
  role: '项目协作负责人'
}

export const mockAgents = [
  { id: 'tiangong', name: '天工｜Agent Router', avatar: '/static/tiangong-avatar.png', role: '路由调度', slogan: '把目标拆清，把上下文配齐。', duty: '推荐上下文、Skill、Agent 和模型，并展示每次任务的执行链路。', status: 'online', lastResult: '完成今日任务上下文与 Agent 分派' },
  { id: 'guanwei', name: '观微｜Context Engine', avatar: '/static/guanwei.png', role: '上下文引擎', slogan: '先组装上下文，再开始执行。', duty: '为任务自动组装需求、代码、文档、历史经验和相关 Skill。', status: 'online', lastResult: '生成支付回调修复 Context Pack，命中 6 条 Memory' },
  { id: 'zhiju', name: '执矩｜Task Execution', avatar: '/static/zhiju.png', role: '任务执行', slogan: '人机协作，过程可追踪。', duty: '管理任务、分派成员与 Agent、记录执行过程和关键决策。', status: 'online', lastResult: '为权限改造任务生成 5 步执行流' },
  { id: 'bowen', name: '博闻｜Team Memory', avatar: '/static/bowen.png', role: '团队记忆', slogan: '经验可复用，记忆可计算。', duty: '保存团队决策、问题、尝试、根因、方案、适用条件和验证记录。', status: 'busy', lastResult: '4 条 Memory Unit 等待人工审核' },
  { id: 'heming', name: '和鸣｜Memory Evolution', avatar: '/static/heming.png', role: '记忆演化', slogan: '从过程里长出方法。', duty: '从任务记录、Bug、PR 和聊天中提炼可复用经验，生成 Skill 候选。', status: 'online', lastResult: '识别 2 个重复问题可资产化' },
  { id: 'mingjian', name: '明鉴｜Eval Lab', avatar: '/static/mingjian.png', role: '评测核查', slogan: '有效才沉淀，稳定才推广。', duty: '验证 Skill 是否有效，比较版本质量、成本、成功率和回归表现。', status: 'online', lastResult: '最近一次 Skill 回归通过率 92%' }
]

export const mockTasks = [
  {
    id: 1,
    workOrderNo: 'TM-20260907-001',
    title: '支付回调偶发重复扣款修复',
    equipment_name: '支付服务',
    equipment_no: 'repo/payment-service',
    equipment_model: 'Node.js + MySQL',
    equipment_category: '后端服务',
    fault_code: 'BUG-421',
    fault_type: '线上 Bug',
    description: '回调重试时幂等键缺失，少量订单出现重复处理风险，需要人和 Agent 联合修复。',
    project_phase: '需求澄清与影响面评估',
    project_period: '2026-09-07 ~ 2026-09-12',
    projectProgressSummary: '已完成线上日志抽样、订单影响范围初判和 Context Pack 组装，等待确认修复边界。',
    latest_update: '09:30 已锁定重复处理链路，正在补齐幂等验证用例',
    next_milestone: '9 月 8 日提交修复 PR 与回归用例',
    deliverables: ['影响面报告', '修复 PR', '幂等回归用例', '支付回调 Memory'],
    risks: ['涉及资金链路', '灰度窗口短', '历史订单需回放验证'],
    severity: 'high',
    status: 'pending',
    assignee_name: '聪明的一休',
    collaborators: ['Context Engine', 'Eval Lab'],
    current_step: 'Context Pack 生成',
    progress: 18,
    due_at: '2026-09-07 18:00',
    created_at: '2026-09-07 09:30',
    image: '/static/industrial-banner-1.png',
    tools: ['日志检索', 'PR Diff', '回归用例'],
    parts: ['幂等校验 Skill', '支付回调 Memory'],
    safety: ['影响面确认', '灰度发布', '回滚方案'],
    sop: ['组装上下文', '定位根因', '生成修复方案', '提交 PR', '运行 Eval', '沉淀 Memory'],
    recheck: { status: 'waiting', result: '', comment: '' }
  },
  {
    id: 2,
    workOrderNo: 'TM-20260907-002',
    title: '权限模型重构任务',
    equipment_name: '成员权限模块',
    equipment_no: 'repo/team-console',
    equipment_model: 'Vue + Flask',
    equipment_category: '前后端协作',
    fault_code: 'PR-118',
    fault_type: '功能改造',
    description: '把项目、任务、Memory、Skill 的权限边界统一，避免人工重复解释上下文。',
    project_phase: '核心开发',
    project_period: '2026-09-05 ~ 2026-09-15',
    projectProgressSummary: '后端权限模型已完成草案，前端状态与路由守卫正在对齐，接口契约待评审。',
    latest_update: '已完成成员角色矩阵，正在同步项目级资源访问规则',
    next_milestone: '9 月 10 日完成接口联调与权限回归',
    deliverables: ['权限矩阵', '接口契约', '前端路由守卫', '审计记录方案'],
    risks: ['旧数据迁移', '跨模块权限边界', '测试用例覆盖不足'],
    severity: 'medium',
    status: 'in_progress',
    assignee_name: '王铭',
    collaborators: ['聪明的一休', 'Agent Router'],
    current_step: '执行链路同步',
    progress: 56,
    due_at: '2026-09-07 20:00',
    created_at: '2026-09-07 08:15',
    image: '/static/equipment.png',
    tools: ['Schema Diff', '接口契约', '用例矩阵'],
    parts: ['权限决策 Memory', '路由策略 Skill'],
    safety: ['数据隔离', '最小权限', '审计记录'],
    sop: ['梳理需求', '改造接口', '更新前端状态', '补充回归用例', '记录决策'],
    recheck: { status: 'waiting', result: '', comment: '' }
  },
  {
    id: 3,
    workOrderNo: 'TM-20260907-003',
    title: '登录失败重复问题资产化',
    equipment_name: '登录链路',
    equipment_no: 'issue/auth-77',
    equipment_model: 'JWT + Session',
    equipment_category: '问题演化',
    fault_code: 'ISSUE-77',
    fault_type: '重复问题',
    description: '多次任务都出现 token 过期提示不清晰，需要转成 Memory 和 Skill 候选。',
    project_phase: '验收评测',
    project_period: '2026-09-06 ~ 2026-09-09',
    projectProgressSummary: '重复问题已聚类，Memory 草稿和 Skill 候选已生成，正在进入 Eval Lab 验证。',
    latest_update: '已补充 6 个登录失败样例，等待人工审核适用边界',
    next_milestone: '9 月 8 日完成 Skill 回归并决定是否入库',
    deliverables: ['问题聚类报告', 'Memory Unit', '认证排查 Skill', 'Eval 记录'],
    risks: ['样例覆盖不够', '错误提示与安全策略冲突'],
    severity: 'medium',
    status: 'review',
    assignee_name: '陈程',
    collaborators: ['Memory Evolution'],
    current_step: 'Skill 回归评测',
    progress: 86,
    due_at: '2026-09-08 10:00',
    created_at: '2026-09-06 14:20',
    image: '/static/industrial-banner-2.png',
    tools: ['Issue 聚类', '聊天摘要', '验收用例'],
    parts: ['登录错误 Memory', '认证排查 Skill'],
    safety: ['隐私脱敏', '人工审核'],
    sop: ['聚类重复问题', '提炼根因', '生成 Skill 草案', '执行 Eval', '审核入库'],
    recheck: { status: 'waiting', result: '', comment: '' }
  },
  {
    id: 4,
    workOrderNo: 'TM-20260906-009',
    title: '日报生成 Skill 回归',
    equipment_name: '项目日报 Skill',
    equipment_no: 'skill/daily-report',
    equipment_model: 'Prompt + Workflow',
    equipment_category: 'Skill 资产',
    fault_code: '',
    fault_type: '回归评测',
    description: '比较日报 Skill v1.3 和 v1.4 的质量、耗时和成本。',
    project_phase: '已归档',
    project_period: '2026-09-06 ~ 2026-09-06',
    projectProgressSummary: '已完成新旧版本对照评测，v1.4 在一致性和可读性上更优，结果已归档。',
    latest_update: 'Eval 通过，日报 Skill v1.4 已发布为默认版本',
    next_milestone: '下周补充成本监控指标',
    deliverables: ['对照评测表', '评分 Rubric', '发布记录'],
    risks: ['后续需观察长文本稳定性'],
    severity: 'low',
    status: 'completed',
    assignee_name: '唐忆哲',
    collaborators: [],
    current_step: '归档',
    progress: 100,
    due_at: '2026-09-06 17:00',
    created_at: '2026-09-06 09:00',
    image: '/static/industrial-banner-3.png',
    tools: ['样例集', '评分 Rubric'],
    parts: ['日报 Skill v1.4'],
    safety: ['结果可复现'],
    sop: ['加载样例集', '运行旧版', '运行新版', '对比分数', '发布版本'],
    recheck: { status: 'passed', result: '通过', comment: '新版成功率和一致性更高' }
  }
]

export const mockKnowledge = [
  { id: 'kb-001', title: '支付回调幂等处理 Memory Unit', type: 'Memory Unit', category: '根因与方案', equipment: '支付服务', model: 'Node.js + MySQL', match: 96, updated_at: '2026-09-06', source: 'BUG-421 复盘', summary: '记录重复扣款的触发条件、根因、修复方案、验证方式和适用边界。', tags: ['支付', '幂等', '根因'], citations: 89, fileType: 'MD', status: 'approved' },
  { id: 'kb-002', title: '权限改造 Context Pack 模板', type: 'Skill', category: '任务上下文', equipment: '成员权限模块', model: 'Vue + Flask', match: 92, updated_at: '2026-09-05', source: '标准 Skill 库', summary: '定义权限改造任务需要自动召回的需求、接口、Schema、测试和历史决策。', tags: ['权限', 'Context Pack', 'Skill'], citations: 78, fileType: 'YAML', status: 'approved' },
  { id: 'kb-003', title: '登录失败提示重复问题记录', type: 'Issue to Skill', category: '问题资产化', equipment: '登录链路', model: 'JWT + Session', match: 88, updated_at: '2026-09-04', source: 'Issue 聚类', summary: '整理多次登录失败任务中的尝试、误判、最终根因和可复用排查路径。', tags: ['认证', '重复问题', 'Skill 候选'], citations: 34, fileType: 'MD', status: 'pending' },
  { id: 'kb-004', title: 'Skill 回归评测 Rubric', type: 'Eval Case', category: 'Eval Lab', equipment: '项目日报 Skill', model: 'Prompt + Workflow', match: 84, updated_at: '2026-09-03', source: 'Eval Lab', summary: '包含成功率、成本、耗时、一致性和人工可读性的评分规则。', tags: ['Eval', 'Rubric', '回归'], citations: 120, fileType: 'JSON', status: 'approved' }
]

export const mockFiles = [
  { id: 'file-001', name: '支付回调 BUG-421 复盘.md', type: 'Markdown', category: 'Memory Unit', folder: '支付服务', size: '48 KB', equipment: '支付服务', model: 'Node.js + MySQL', uploader: '聪明的一休', uploaded_at: '2026-09-06 10:12', updated_at: '2026-09-06 11:30', auditStatus: '已通过', parseStatus: '解析成功', version: 'v1.2', knowledgeLinks: 8, downloads: 36, url: '', favorite: true },
  { id: 'file-002', name: '权限改造 Context Pack 模板.yaml', type: 'YAML', category: 'Skill', folder: '成员权限模块', size: '26 KB', equipment: '成员权限模块', model: 'Vue + Flask', uploader: '唐忆哲', uploaded_at: '2026-09-05 16:40', updated_at: '2026-09-05 16:40', auditStatus: '审核中', parseStatus: '解析中', version: 'v1.0', knowledgeLinks: 3, downloads: 12, url: '', favorite: false },
  { id: 'file-003', name: '登录失败 Issue 聚类报告.png', type: '图片', category: 'Issue to Skill', folder: '登录链路', size: '2.4 MB', equipment: '登录链路', model: 'JWT + Session', uploader: '陈程', uploaded_at: '2026-09-04 09:18', updated_at: '2026-09-04 09:18', auditStatus: '已通过', parseStatus: '部分成功', version: 'v1.0', knowledgeLinks: 1, downloads: 5, url: '/static/industrial-banner-2.png', favorite: false }
]

export const mockContacts = [
  { id: 1, name: '聪明的一休', avatar: '/static/avatar-1.png', position: '协作负责人', department: 'AI 原生项目协作组', specialty: 'Context/Memory', phone: '138-0000-1024', status: '在线', currentTask: '支付回调修复', devices: ['支付服务', '权限模块'], workload: 72 },
  { id: 2, name: '唐忆哲', avatar: '/static/avatar-2.png', position: '评测负责人', department: 'Eval Lab', specialty: 'Skill 回归', phone: '138-0000-2048', status: '在线', currentTask: '日报 Skill 回归', devices: ['日报 Skill'], workload: 48 },
  { id: 3, name: '赵宁', avatar: '/static/avatar-3.png', position: 'Memory 审核人', department: 'Team Memory', specialty: '问题资产化', phone: '138-0000-4096', status: '忙碌', currentTask: '重复问题审核', devices: ['登录链路', '支付服务'], workload: 83 }
]

export const mockOverview = {
  status: {
    system: '正常',
    backend: '在线',
    ai: 'Agent Router 可用',
    rag: 'Context Engine 可检索',
    knowledge: '156 条 Memory'
  },
  recent: [
    '生成：支付回调 Context Pack',
    '查看：权限改造 Skill 模板',
    '沉淀：登录失败重复问题',
    '评测：日报 Skill v1.4'
  ],
  trend: [9, 12, 8, 15, 18, 14, 20],
  faultDistribution: [
    { label: '线上 Bug', value: 32 },
    { label: '功能改造', value: 26 },
    { label: '重复问题', value: 18 },
    { label: 'Skill 回归', value: 14 },
    { label: '其他', value: 10 }
  ]
}

export const mockSearchResult = {
  phenomenonSummary: '已为当前任务组装需求、代码、文档、历史经验和相关 Skill，形成可执行 Context Pack。',
  causes: ['历史任务中出现过相同幂等边界', '接口契约与数据库约束没有同步更新', '缺少覆盖重试场景的回归 Eval', '已有支付回调 Memory 可复用'],
  parts: ['需求说明', '接口代码', '数据库约束', '历史 PR', '相关 Skill'],
  risk: 'medium',
  confidence: 88,
  positions: ['回调入口', '订单状态表', '重试队列', '历史复盘记录'],
  methods: ['相似任务召回', '代码路径分析', 'Memory 匹配', 'Eval 用例生成'],
  tools: ['Context Engine', 'PR Diff', '日志片段', 'Skill 模板'],
  safety: ['确认影响范围', '脱敏日志', '灰度发布', '保留回滚方案'],
  stopAdvice: '建议先冻结相关发布分支，补齐幂等 Eval 后再合并',
  references: mockKnowledge,
  suggestion: {
    diagnosis: '优先复用支付回调幂等 Memory，并把修复过程沉淀为新版 Skill。',
    preparation: ['确认需求和影响范围', '召回相关代码、Issue、PR 和历史决策'],
    tools: ['Context Engine', 'Eval Lab', 'Team Memory'],
    parts: ['幂等键策略', '回归用例', '发布检查清单'],
    steps: ['生成 Context Pack', '定位入口与状态变更', '补充幂等约束', '运行 Skill Eval', '审核 Memory 入库'],
    risks: ['重复扣款', '数据不一致', '未经验证的 Skill 被复用'],
    retest: ['重试请求只处理一次', '订单状态一致', 'Eval 通过率达标']
  }
}

export const createOverviewFromMock = () => {
  const pending = mockTasks.filter((task) => ['pending', 'in_progress'].includes(task.status)).length
  const review = mockTasks.filter((task) => task.status === 'review').length
  const completed = mockTasks.filter((task) => task.status === 'completed').length
  const highRisk = mockTasks.filter((task) => task.severity === 'high' || task.severity === 'critical').length
  return {
    ...mockOverview,
    stats: {
      todayNew: 3,
      pending,
      inProgress: mockTasks.filter((task) => task.status === 'in_progress').length,
      highRisk,
      review,
      completed,
      knowledgeTotal: mockKnowledge.length + 152,
      weekKnowledge: 9,
      onlineUsers: mockContacts.filter((contact) => contact.status === '在线').length,
      skillCoverage: 68,
      newMemories: 9,
      evalPassed: 92,
      repeatWorkDown: 24,
      aiCostSaved: 31
    },
    tasks: mockTasks,
    knowledge: mockKnowledge,
    files: mockFiles,
    agents: mockAgents
  }
}

export const mockSkills = [
  { id: 1, name: 'Machina', category: '工业维护 Agent', trigger: '设备故障诊断', successRate: 94, usedCount: 1280, status: 'verified', version: 'v0.2', description: '用几行 Python 构建工业维护 AI Agent，内置 CMMS、传感器和文档 RAG 连接器。', repo: 'https://github.com/LGDiMaggio/machina', stars: 1200, lang: 'Python' },
  { id: 2, name: 'Graphiti', category: '知识图谱', trigger: '实时上下文记忆', successRate: 97, usedCount: 30858, status: 'verified', version: 'v1.0', description: '为 AI Agent 构建时序知识图谱，跟踪事实随时间的变化，支持混合检索。', repo: 'https://github.com/getzep/graphiti', stars: 30858, lang: 'Python' },
  { id: 3, name: 'Microsoft GraphRAG', category: 'RAG 框架', trigger: '文档知识检索', successRate: 95, usedCount: 33900, status: 'verified', version: 'v2.0', description: '微软开源的基于图的 RAG 系统，模块化架构，支持实体提取与社区摘要。', repo: 'https://github.com/microsoft/graphrag', stars: 33900, lang: 'Python' },
  { id: 4, name: 'nanobot', category: 'Agent 框架', trigger: '多 Agent 协作', successRate: 92, usedCount: 47663, status: 'verified', version: 'v0.3', description: '超轻量级开源个人 AI Agent 框架，支持工具调用、长期记忆、MCP 集成和多 Agent 委派。', repo: 'https://github.com/HKUDS/nanobot', stars: 47663, lang: 'Python' },
  { id: 5, name: 'Agentic Predictive Maintenance', category: '预测性维护', trigger: 'IoT 传感器异常', successRate: 88, usedCount: 356, status: 'testing', version: 'v1.0', description: '三 Agent 协作的工业预测性维护系统，结合 RAG 检索技术文档与故障根因分析。', repo: 'https://github.com/fhattat/agentic-pred-maintenance-rag', stars: 356, lang: 'Python' },
  { id: 6, name: 'FlowGuard Engine', category: '安全关键系统', trigger: '电梯遥测异常', successRate: 91, usedCount: 890, status: 'verified', version: 'v1.0', description: '安全优先的数字孪生诊断引擎，LangGraph + Qdrant + FastAPI，带安全防护栏自动重试。', repo: 'https://github.com/Nibir1/FlowGuard-Engine', stars: 890, lang: 'Python' },
]

