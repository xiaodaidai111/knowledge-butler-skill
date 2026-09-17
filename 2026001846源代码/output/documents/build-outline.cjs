const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, Header, Footer, HeadingLevel, AlignmentType, PageNumber } = require('C:/Users/artists/AppData/Roaming/npm/node_modules/docx');

const sections = [
  ['（一）产品概述与定位', [
    ['背景与目标', '介绍研发过程中的知识分散、上下文重复整理、经验随人员流失、AI 输出难以持续复用等问题；提出建设团队共同记忆、组织人机协作、实现经验验证与复用的研发目标。'],
    ['产品定位与目标用户', '定位为 AI 原生项目协作与团队记忆系统，面向软件研发团队、高校项目团队及企业内部技术团队，服务需求分析、功能开发、问题修复、测试评审和新人接手等场景。'],
    ['核心概念与业务闭环', '定义任务、上下文包、记忆单元、Skill 和评测记录：记忆单元保存经验及适用条件，Skill 将经验组织为可执行流程，评测记录提供有效性证据。'],
    ['产品特色与设计原则', '突出任务驱动的上下文供给、过程可追踪的 Agent 协作、包含失败原因的结构化记忆，以及经过评测再复用的能力积累机制；坚持来源可查、权限可控、关键操作人工确认。'],
  ]],
  ['（二）技术架构与创新', [
    ['系统整体架构', '按照交互层、业务服务层、AI 能力层、数据存储层与安全治理层展开，绘制系统架构图，说明浏览器、后端接口、模型服务、检索服务和数据库之间的关系。'],
    ['前后端及 AI 技术选型', '基于现有 Vue 3、Vite、ECharts 和 Flask 工程，说明界面、接口与可视化选型；说明 Qwen/DashScope、模型调用封装及 RAG 相关实现的职责与适用范围。'],
    ['数据架构与交互流程', '梳理用户、项目、任务、上下文包、Memory、Skill 版本、评测用例、评测运行和路由日志的关联；说明当前 SQLite 业务存储与 MySQL 配置的实际使用边界及后续统一方案。'],
    ['上下文与智能体协作机制', '设计任务解析、资料召回、结果筛选、上下文预算分配、Agent 分派和执行反馈流程，说明任务状态、工具调用、审批与异常恢复如何协同。'],
    ['核心创新与对比验证', '围绕“任务上下文自动组装”“失败经验结构化沉淀”“问题到 Skill 的演化”“评测约束下的复用”提出创新点；通过功能对照和实验验证，与传统项目管理、文档知识库及通用 AI 聊天工具比较。'],
  ]],
  ['（三）功能设计与实现', [
    ['首页：项目协作工作台', '集中展示任务进度、待办事项、最近活动、记忆沉淀和评测动态；提供常用入口与资料轮播，帮助用户进入当前工作。'],
    ['上下文引擎：任务上下文包生成', '接收任务描述及附件，检索相关文档、历史任务与团队记忆，组织任务摘要、引用依据、约束条件和推荐 Skill；代码仓库、PR 与聊天数据按接入进度扩展。'],
    ['任务执行中心：人机协作任务管理', '支持任务创建、负责人分派、执行阶段流转和结果验收；关联上下文包、参与 Agent、执行记录、产出附件与验证结果。'],
    ['团队记忆库：结构化经验管理', '围绕问题、背景、尝试、失败原因、根因、解决方案、适用条件和验证证据保存记忆单元，支持检索、编辑、版本追踪及来源关联。'],
    ['记忆演化引擎：经验抽取与审核', '设计从任务记录、问题讨论和执行日志中抽取候选经验的流程，经过去重、关联和人工审核后入库，并对过时或冲突记忆进行修订。'],
    ['Skill 工厂：可复用流程生成与管理', '将已验证经验整理为包含触发条件、输入要求、执行步骤、工具依赖和验收标准的 Skill，管理草稿、版本、发布及停用状态。'],
    ['评测中心：Skill 有效性验证', '管理测试用例、预期结果和运行记录，对比不同 Skill 版本的成功率、质量、耗时及调用成本，为发布、回退和优化提供依据。'],
    ['问题演化系统：Issue 到 Memory 与 Skill', '识别重复问题，关联历史尝试与解决记录，推动问题归类、根因整理、记忆更新、Skill 修订和回归验证，形成可追踪的改进链路。'],
    ['Agent / Router 操作面板', '结合任务类型推荐 Agent、模型和工具，展示执行步骤、调用结果与审批状态；逐步完善按质量、成本和时延约束进行路由的策略。'],
    ['个人中心与公共支撑功能', '个人中心展示个人任务、收藏、贡献记录和偏好设置；公共能力包含身份认证、项目权限、文件管理、消息通知和操作审计，团队统计按授权范围展示。'],
    ['扩展性设计', '预留模型适配、资料来源接入、工具注册和评测器扩展接口，规划代码托管平台集成、多模态资料解析及不同研发场景的 Skill 模板。'],
  ]],
  ['（四）开发测试与部署', [
    ['开发流程与团队分工', '按需求与原型、基础业务、AI 集成、记忆与 Skill 闭环、测试部署划分阶段；明确前端、后端、AI、数据和测试职责，并以实际研发记录填写时间节点与交付物。'],
    ['关键代码与工程实现', '选取上下文生成、模型调用、任务状态流转、记忆写入和审批校验等代表性代码，说明接口契约、输入校验、错误处理、幂等控制和日志追踪。'],
    ['功能与 AI 专项测试', '覆盖任务流转、记忆版本、权限隔离及失败恢复；专项验证检索相关性、引用准确性、经验抽取完整性、Skill 执行成功率和 Agent 工具调用正确性。'],
    ['对照实验与优化方法', '设置无团队记忆、仅检索增强、记忆与 Skill 联合使用等对照条件，在统一任务集上记录结果；根据失败案例优化召回、上下文组织、提示词与 Skill 步骤，避免测试数据泄漏。'],
    ['性能、安全与部署方案', '提供本地演示和服务器部署流程，说明前端构建、后端运行、数据库初始化、模型配置、文件持久化与备份恢复；验证并发请求、超时、访问控制和提示注入防护。'],
    ['验证证据与交付材料', '整理测试用例表、真实运行结果、缺陷修复记录、页面截图、部署说明和演示脚本，明确测试环境、模型版本、样本数量及已知限制。'],
  ]],
  ['（五）应用价值与展望', [
    ['典型应用场景', '围绕新人接手项目、重复 Bug 修复、新功能协作开发和测试经验复用，分别描述输入资料、操作步骤、人机分工、系统产出及验收方式。'],
    ['应用价值与量化评价', '评估上下文准备时长、任务完成时长、重复问题处理时长、记忆复用率、Skill 成功率和单任务 AI 成本；交代统计口径、比较基线与样本来源。'],
    ['市场与竞争分析', '分析目标团队的需求、采用门槛及推广路径，对比项目管理工具、知识管理平台和 AI 编程助手；市场规模、产品能力及趋势判断引用可核验资料。'],
    ['成果总结与经验回顾', '按已实现、已验证和待完善三类整理成果，展示代表性业务闭环与案例，归纳上下文组织、经验结构化、Agent 协作及前后端联动中的实践经验。'],
    ['当前不足与未来规划', '近期完善真实数据闭环、历史业务清理和评测记录；中期推进仓库接入、Skill 自动生成与模型路由；长期探索跨项目经验迁移和私有化部署，各阶段明确验收条件。'],
  ]],
];

const body = text => new Paragraph({ spacing: { after: 120, line: 360 }, indent: { firstLine: 480 }, children: [new TextRun(text)] });
const children = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 180 }, children: [new TextRun({ text: '一休', bold: true, size: 44, font: '黑体' })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: '面向研发团队的共同记忆演化与人机协作系统', bold: true, size: 28, font: '黑体' })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 320 }, children: [new TextRun({ text: '技术方案参考大纲', size: 28 })] }),
  body('核心主线：任务提出 → 上下文组装 → 人与 Agent 协作 → 经验沉淀 → Skill 生成 → 评测验证 → 再次复用。'),
  body('编写说明：本文件为技术方案展开提纲。现有工程已有页面、任务与知识管理、智能体接口及相关数据表基础；自动 Skill 演化、完整回归评测和成本收益等内容，应按实际验证情况区分“已实现”和“规划”，不能将演示指标作为实测成果。'),
  new Paragraph({ heading: HeadingLevel.HEADING_1, text: '五、技术方案' }),
];
for (const [title, items] of sections) {
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, text: title }));
  items.forEach(([name, text], i) => {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, text: `${i + 1}. ${name}` }));
    children.push(body(text));
  });
}
const doc = new Document({
  creator: '一休项目组', title: '一休系统技术方案大纲', description: '面向研发团队的共同记忆演化与人机协作系统技术方案参考大纲',
  styles: {
    default: { document: { run: { font: { ascii: 'Arial', hAnsi: 'Arial', eastAsia: '宋体' }, size: 24, color: '222222' }, paragraph: { widowControl: true } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: '黑体', size: 34, bold: true, color: '000000' }, paragraph: { outlineLevel: 0, keepNext: true, spacing: { before: 300, after: 200 } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: '黑体', size: 30, bold: true, color: '000000' }, paragraph: { outlineLevel: 1, keepNext: true, spacing: { before: 260, after: 160 } } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: '黑体', size: 25, bold: true, color: '000000' }, paragraph: { outlineLevel: 2, keepNext: true, spacing: { before: 160, after: 80 } } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1247, bottom: 1247, left: 1417, right: 1417 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: '一休 | 系统技术方案大纲', size: 18, color: '666666' })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '第 ', size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 }), new TextRun({ text: ' 页', size: 18 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(buffer => {
  const output = path.join(__dirname, '一休系统技术方案大纲.docx');
  fs.writeFileSync(output, buffer);
  console.log(JSON.stringify({ output, bytes: buffer.length, sections: sections.length, subsections: sections.reduce((sum, item) => sum + item[1].length, 0) }));
}).catch(error => { console.error(error); process.exitCode = 1; });
