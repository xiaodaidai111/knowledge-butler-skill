# 一修 Web 系统向 TeamMemory OS 的模块改造说明

## 1. 新系统定位

当前一修 Web 系统本质是“设备检修知识检索与作业系统”，已有首页工作台、智能检索、检修任务、知识库、个人中心、AIOS 智能体、知识沉淀、任务流转等基础能力。

新的系统设计可以升级为：

**TeamMemory OS：团队共同记忆演化与 AI 协作系统。**

它不再只服务设备检修，而是服务团队项目协作。核心闭环从：

**故障检索 → 工单执行 → 知识沉淀**

升级为：

**任务产生 → 上下文组装 → 人 / AI Agent 执行 → 过程记录 → 记忆沉淀 → Skill 生成 → Eval 验证 → 下次自动复用。**

一句话定位：

**把团队每一次人类与 AI 的协作，持续转化为下一次任务可以复用的能力。**

## 2. 现有模块到新模块的改造总表

| 当前一修模块 | 改造成的新模块 | 新模块作用 | 改造重点 |
| --- | --- | --- | --- |
| 首页 / 综合工作台 | Project Hub 项目工作台 | 汇总项目、任务、成员、Agent、Memory、Skill、Eval 状态 | 从“今日检修任务”改为“项目智能运行态势” |
| 智能检索 | Context Engine 上下文引擎 | 为任务自动组装需求、代码、文档、历史经验、相关 Skill | 从“设备故障检索”改为“任务上下文包生成” |
| 检修任务 | Task Execution 任务执行中心 | 管理任务、分派人和 Agent、记录执行过程 | 从“工单闭环”改为“人机协作任务闭环” |
| 知识库 | Team Memory 团队记忆库 | 保存团队决策、问题、尝试、根因、方案、适用条件和验证记录 | 从“资料文档库”改为“可计算的 Memory Unit 库” |
| 知识沉淀 | Memory Evolution 记忆演化引擎 | 从任务记录、Bug、PR、聊天中提炼可复用经验 | 从“人工填表沉淀”改为“自动抽取 + 人工审核” |
| AIOS 智能体 | Agent Collaboration Center 智能体协作中心 | 统一编排 Planner、Developer、Reviewer、QA、Memory、Skill 等 Agent | 从“检修智能体”改为“项目协作多 Agent” |
| 文档模板 | Skill Factory 技能工厂 | 把高频成功经验变成可执行 Skill | 从“报告模板”改为“团队 SOP / Skill 生成器” |
| 复检 / 核查 | Eval Lab 评测中心 | 验证 Skill 是否有效，比较版本质量、成本、成功率 | 从“检修复检”改为“Skill 回归评测” |
| 任务风险 / 高风险提醒 | Issue to Skill 问题演化系统 | 把 Bug、失败任务、重复问题转成 Memory 和 Skill | 从“风险等级”改为“重复问题识别和资产化” |
| 右侧 AI 助手 | Agent / Router 操作面板 | 推荐上下文、Skill、Agent、模型，并展示执行链路 | 从“聊天框”改为“工作流智能辅助层” |
| 图表看板 | Team Intelligence 团队智能分析 | 统计 Skill 覆盖率、重复劳动率、AI 成本、团队能力沉淀 | 从“检修数据看板”改为“团队能力增长看板” |

## 3. 前端页面改造建议

### 3.1 首页改为 Project Hub 项目工作台

当前首页展示的是设备检修任务、风险、日程、知识沉淀和系统概览。

应改成：

**Project Hub 项目工作台**

作用：

- 展示当前项目的整体状态。
- 汇总活跃任务、Agent 执行任务、今日新增 Memory、使用的 Skill、Eval 通过情况。
- 让用户一打开系统就知道团队正在如何协作、哪些经验正在沉淀、哪些 Skill 正在被复用。

页面内容建议：

| 当前内容 | 改造成 |
| --- | --- |
| 今日检修任务 | 今日项目任务 |
| 高风险待确认 | 高风险任务 / 高风险变更 |
| 本周知识沉淀 | 本周新增 Team Memory |
| 工作轨迹 | AI Activity 执行动态 |
| 数据分析看板 | Team Intelligence 指标 |
| 检修日程 | 项目里程碑 / Sprint 节点 |

核心指标：

- Active Tasks：活跃任务数。
- Agent Tasks：AI 正在执行的任务数。
- Skills Used：今日复用 Skill 次数。
- New Memories：新增团队记忆数。
- Eval Passed：通过评测的 Skill 数。
- Repeat Work Down：重复劳动下降比例。
- AI Cost Saved：AI 成本节约比例。

### 3.2 智能检索改为 Context Engine 上下文引擎

当前智能检索围绕设备、型号、故障代码、现场图片、维修资料生成故障研判。

应改成：

**Context Engine 上下文引擎**

作用：

- 用户输入一个任务，系统自动查找相关需求、代码、文档、历史 PR、Issue、Memory、Skill。
- 生成给人或 AI Agent 使用的 Context Pack。

页面内容建议：

| 当前字段 | 改造成 |
| --- | --- |
| 设备名称 | 项目 / 仓库 |
| 设备型号 | 技术栈 / 模块 |
| 故障类型 | 任务类型 |
| 故障代码 | Issue / PR / Ticket ID |
| 故障现象 | 用户需求 / 问题描述 |
| 现场附件 | 需求文档、错误日志、截图、代码片段 |
| 研判结论 | Context Pack 摘要 |
| 引用依据 | 相关 Memory、Skill、代码文件、历史任务 |

Context Pack 应包含：

- Task Summary：任务摘要。
- Relevant Files：相关文件。
- Related Issues：历史问题。
- Related Decisions：相关决策。
- Matching Memories：匹配记忆。
- Recommended Skills：推荐 Skill。
- Suggested Agents：建议调用的 Agent。
- Risk Notes：风险提示。

### 3.3 检修任务改为 Task Execution 任务执行中心

当前检修任务管理设备工单、负责人、状态、SOP、复检。

应改成：

**Task Execution 任务执行中心**

作用：

- 管理团队任务。
- 支持人工成员和 AI Agent 共同执行。
- 完整记录任务从创建、规划、执行、Review、Eval、沉淀的全过程。

页面内容建议：

| 当前内容 | 改造成 |
| --- | --- |
| 检修工单 | 项目任务 |
| 设备编号 | 仓库 / 模块 |
| 故障类型 | 任务类型：Feature、Bug、Refactor、Research |
| 当前步骤 | 执行阶段：Plan、Implement、Review、Test、Memory |
| SOP 步骤 | 推荐 Skill 执行步骤 |
| 复检 | Eval / QA 验证 |
| 联系人协作 | 成员 + Agent 协作 |

任务详情页应成为核心页面，包含：

- Requirement：需求。
- Context Pack：上下文包。
- Agents：Planner、Developer、Reviewer、QA、Memory Agent。
- Execution Timeline：执行时间线。
- Used Skill：使用了哪个 Skill。
- Result：产出。
- Eval Result：验证结果。
- Generate Memory：生成记忆。
- Update Skill：更新 Skill。

### 3.4 知识库改为 Team Memory 团队记忆库

当前知识库保存维修手册、历史案例、SOP、安全规范。

应改成：

**Team Memory 团队记忆库**

作用：

- 保存团队的隐性经验。
- 不只是文档，而是结构化、可检索、可复用、可演化的 Memory Unit。

Memory Unit 字段建议：

| 字段 | 含义 |
| --- | --- |
| title | 记忆标题 |
| project | 所属项目 |
| task_id | 来源任务 |
| issue_id | 来源问题 |
| context | 当时上下文 |
| problem | 遇到的问题 |
| attempts | 尝试过的方案 |
| failed_reasons | 失败原因 |
| root_cause | 根因 |
| solution | 最终方案 |
| applicable_when | 适用条件 |
| not_applicable_when | 不适用条件 |
| related_files | 关联文件 |
| related_commits | 关联提交 |
| source_people | 来源人员 |
| source_agents | 来源 Agent |
| verification_count | 验证次数 |
| success_rate | 成功率 |
| skill_candidates | 可生成的 Skill |
| status | draft / reviewed / verified / deprecated |

### 3.5 知识沉淀页改为 Memory Evolution 记忆演化页

当前知识沉淀主要是把检索结果填成知识条目。

应改成：

**Memory Evolution 记忆演化引擎**

作用：

- 从任务执行记录、Bug 处理过程、Review 反馈、失败原因中自动提炼 Memory。
- 识别重复问题，建议生成 Skill。

流程：

1. 读取任务执行记录。
2. 识别关键上下文。
3. 提取问题、尝试、根因、解决方案。
4. 生成 Memory Draft。
5. 人工审核。
6. 判断是否转成 Skill Candidate。
7. 进入 Eval Lab。

### 3.6 AIOS 改为 Agent Collaboration Center 智能体协作中心

当前 AIOS 已经有 Agent、Team、Session、Memory、Approval、Trace、Plan、Execute 等接口基础。

应改成：

**Agent Collaboration Center 智能体协作中心**

作用：

- 统一管理团队中不同角色的 AI Agent。
- 根据任务自动分派 Agent。
- 记录每个 Agent 的输入、输出、工具调用和结果。

建议 Agent：

| Agent | 作用 |
| --- | --- |
| PM Agent | 拆解需求、识别范围、生成任务 |
| Planner Agent | 制定执行计划 |
| Developer Agent | 编码或执行操作 |
| Reviewer Agent | 代码审查和风险识别 |
| QA Agent | 生成测试、运行验证 |
| Memory Agent | 提炼团队记忆 |
| Skill Agent | 生成或更新 Skill |
| Eval Agent | 构造评测集并打分 |
| Router Agent | 选择 Skill、Agent 和模型 |

### 3.7 文档模板改为 Skill Factory 技能工厂

当前系统有模板接口和知识模板能力。

应改成：

**Skill Factory 技能工厂**

作用：

- 把高频成功经验变成可执行 Skill。
- Skill 不是 Prompt 收藏夹，而是团队 SOP。

Skill 字段建议：

| 字段 | 含义 |
| --- | --- |
| name | Skill 名称 |
| trigger | 触发条件 |
| applicable_when | 适用场景 |
| input_schema | 输入要求 |
| context_requirements | 必要上下文 |
| steps | 执行步骤 |
| tools | 可调用工具 |
| examples | 成功案例 |
| failure_cases | 失败案例 |
| output_schema | 输出要求 |
| eval_cases | 评测用例 |
| dependencies | 依赖 |
| version | 版本 |
| status | candidate / testing / verified / production / deprecated |

典型 Skill：

- API Bug Diagnosis Skill。
- Database Migration Check Skill。
- PR Review Skill。
- Excel Export Implementation Skill。
- Frontend White Screen Debug Skill。
- Requirements to Task Breakdown Skill。

### 3.8 复检模块改为 Eval Lab 评测中心

当前复检用于验证检修任务是否完成。

应改成：

**Eval Lab 评测中心**

作用：

- 验证 Skill 是否真的有效。
- 对 Skill 不同版本做回归测试。
- 根据成功率、质量、成本、耗时决定是否发布。

Eval 指标：

- success_rate：成功率。
- regression_count：回归失败数。
- average_tokens：平均 Token。
- average_cost：平均成本。
- average_latency：平均耗时。
- quality_score：质量评分。
- human_review_score：人工评分。
- failure_patterns：失败模式。

Skill 状态流转：

**Candidate → Testing → Verified → Production → Deprecated**

### 3.9 高风险任务改为 Issue to Skill 问题演化系统

当前系统有高风险、待复检、故障任务等状态。

应改成：

**Issue to Skill 问题演化系统**

作用：

- 把 Bug、线上事故、重复错误变成团队资产。
- 形成 Bug → RCA → Memory → Skill → Eval 的闭环。

流程：

1. 捕获 Issue。
2. 生成 RCA。
3. 记录尝试方案和根因。
4. 形成 Memory Unit。
5. 判断是否是高频问题。
6. 生成 Skill Candidate。
7. Eval 验证。
8. 下次同类任务自动调用。

### 3.10 右侧 AI 助手改为 Skill First Router 操作面板

当前右侧 AI 助手是对话式辅助。

应改成：

**Skill First Router 操作面板**

作用：

- 不优先聊天，而是优先判断“团队过去有没有做过”。
- 如果有 Skill，就推荐 Skill + 低成本模型。
- 如果没有 Skill，再调用大模型探索，并把探索过程沉淀为 Memory。

路由逻辑：

1. 识别任务类型。
2. 搜索 Team Memory。
3. 搜索 Skill Registry。
4. 评估风险和复杂度。
5. 选择 Agent。
6. 选择模型。
7. 执行并记录。
8. 触发 Eval 或 Memory Update。

核心原则：

**Skill First, Model Second.**

## 4. 后端接口改造建议

当前后端已有 `server/backend/routes/yixiu.py`，里面包含 `/overview`、`/tasks`、`/knowledge`、`/aios/*`、`/templates`、`/contacts` 等接口。

可以按以下方式演化：

| 当前接口 | 新接口 | 作用 |
| --- | --- | --- |
| `/api/yixiu/overview` | `/api/team-os/projects/overview` | 项目工作台概览 |
| `/api/yixiu/search` | `/api/team-os/context/pack` | 生成任务上下文包 |
| `/api/yixiu/tasks` | `/api/team-os/tasks` | 项目任务管理 |
| `/api/yixiu/knowledge` | `/api/team-os/memories` | 团队记忆库 |
| `/api/yixiu/knowledge/update` | `/api/team-os/memories/extract` | 从任务记录提炼 Memory |
| `/api/yixiu/templates` | `/api/team-os/skills` | Skill Registry |
| `/api/yixiu/recheck` | `/api/team-os/evals/run` | 运行 Skill 评测 |
| `/api/yixiu/aios/agents` | `/api/team-os/agents` | Agent 管理 |
| `/api/yixiu/aios/plan` | `/api/team-os/routing/plan` | 任务路由计划 |
| `/api/yixiu/aios/execute` | `/api/team-os/routing/execute` | 执行人机协作任务 |
| `/api/yixiu/aios/trace` | `/api/team-os/execution-records` | 执行记录和回放 |

V1 阶段可以不用马上改真实 URL，先在前端和后端内部语义上完成替换；等页面稳定后，再统一迁移接口路径。

## 5. 数据表改造建议

| 当前数据概念 | 新数据概念 | 说明 |
| --- | --- | --- |
| yixiu_tasks | team_tasks | 项目任务 |
| yixiu_knowledge | team_memories | 团队记忆单元 |
| yixiu_knowledge_versions | memory_versions | 记忆版本 |
| yixiu_knowledge_links | memory_links | 记忆与任务、Issue、代码、Skill 的关系 |
| yixiu_doc_templates | team_skills | 技能注册表 |
| yixiu_aios_runs | execution_records | Agent 执行记录 |
| yixiu_aios_queue | agent_task_queue | Agent 任务队列 |
| yixiu_agent_memory | agent_memory | Agent 个人记忆 |
| yixiu_aios_approvals | human_approvals | 高风险操作人工审批 |
| 新增 | eval_cases | Skill 评测用例 |
| 新增 | eval_runs | Skill 评测运行记录 |
| 新增 | model_routing_logs | 模型路由日志 |
| 新增 | task_context_packs | 上下文包快照 |

## 6. 推荐 V1 范围

第一版不要做成超大平台，建议只完成 6 条主线：

1. **Project Hub**
   - 用现有首页改。
   - 展示项目任务、Agent 动态、Memory 数量、Skill 使用量、Eval 结果。

2. **Task Execution**
   - 用现有检修任务页改。
   - 支持任务创建、状态流转、Agent 执行时间线。

3. **Context Engine**
   - 用现有智能检索页改。
   - 输入任务，输出 Context Pack。

4. **Team Memory**
   - 用现有知识库页改。
   - 支持 Memory Unit 的检索、查看、审核、版本。

5. **Skill Factory + Eval Lab**
   - 用现有模板和复检能力改。
   - 支持 Skill Candidate、测试、验证、发布。

6. **Skill First Router**
   - 用现有 AIOS 和右侧助手改。
   - 先匹配 Skill，再选模型和 Agent。

## 7. 实施顺序建议

### 阶段一：只改前端语义和页面结构

目标：

- 用户一打开系统能看到新产品形态。
- 暂时复用 mock 数据和现有 API。

修改内容：

- 首页改为 Project Hub。
- 智能检索改为 Context Engine。
- 检修任务改为 Task Execution。
- 知识库改为 Team Memory。
- 复检/模板入口改为 Skill Factory 和 Eval Lab。

### 阶段二：统一数据模型

目标：

- 把设备检修字段替换成项目协作字段。
- 后端仍可兼容旧字段，但返回新语义。

修改内容：

- 新增 Memory Unit 数据结构。
- 新增 Skill 数据结构。
- 新增 Eval Case / Eval Run。
- 新增 Context Pack。

### 阶段三：打通闭环

目标：

- 一个任务完成后，能自动生成 Memory。
- 高频 Memory 能生成 Skill Candidate。
- Skill 能进入 Eval。

核心闭环：

**Task → Execution Record → Memory Draft → Skill Candidate → Eval → Verified Skill → Next Task Reuse**

### 阶段四：模型路由和成本优化

目标：

- 让系统体现“AI 大材小用”的解决方案。
- 已有 Skill 的任务优先使用低成本模型。
- 未知复杂任务再使用大模型。

路由策略：

**先找 Skill，再选模型。**

## 8. 最小可展示 Demo 剧本

建议演示时走这一条线：

1. 在 Project Hub 创建任务：“实现用户导出 Excel”。
2. Context Engine 自动生成上下文包。
3. Router 检索到历史 Memory：“之前做过 Excel 导出功能”。
4. 系统推荐 Skill：“Excel Export Implementation Skill v3”。
5. Developer Agent 执行。
6. Reviewer Agent 发现一个边界问题。
7. QA Agent 跑 Eval。
8. 任务完成。
9. Memory Agent 生成一条新的 Memory。
10. Skill Agent 建议把 Skill v3 升级到 v4。

这个 Demo 能完整体现：

**团队经验如何被复用、验证、更新和持续进化。**

## 9. 最终改造目标

改造完成后，系统不应该像普通项目管理工具，也不应该像普通 AI 聊天工具。

它应该让用户感受到：

- 团队过去做过的事不会丢。
- 高手经验可以迁移给普通成员。
- AI 不再每次从零开始。
- 成功经验会变成 Skill。
- Skill 会被 Eval 验证。
- 验证过的 Skill 会被下次任务自动复用。
- 团队能力会随着每一次任务持续增长。

最终产品关键词：

**Project Hub、Context Engine、Team Memory、Agent Collaboration、Skill Factory、Eval Lab、Skill First Router、Team Intelligence。**
