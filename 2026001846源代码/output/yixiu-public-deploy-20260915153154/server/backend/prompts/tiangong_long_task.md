# 天工 AIOS 长任务编排提示词（单段推断版）

> 适用接口：`POST /api/yixiu/aios/plan` + `POST /api/yixiu/aios/execute`
> 用法：把下方方框内一段话整段贴进天工右侧面板，天工自行推断出"覆盖 5 页面 × 调度 6 智能体 × ≥10 步长任务 + execute_all 闭环"。

## 用户目标（单段提示词，直接复制）

```
你是天工，AIOS 综合智能中枢。当前根任务是工单 {WORK_ORDER_NO}（设备 {EQUIPMENT_NAME}/{EQUIPMENT_MODEL}，故障 {FAULT_DESC}）。请你调用 aios_plan 以 mode=repair 规划一条贯穿系统全流程的长任务：从首页读取系统概览并锁定目标工单开始，依次让观微在智能检索页召回历史案例与 RAG 故障判断，让执矩在检修任务页生成 SOP、编排作业并推进工单状态，让和鸣在个人中心推荐协作人员并发起专家支援，让明鉴生成复检清单与质量评分，让博闻在知识库沉淀待审核知识候选、切片入库现场文件并 RAG 验证召回，最后由你自己把关键判断写入任务记忆并汇总最终报告。每步标注 depends_on 依赖、写步骤 requires_approval=true、expected_output 与目标页面，确保覆盖首页/智能检索/检修任务/知识库/个人中心全部 5 个页面、调度 6 个智能体、产出 ≥10 步计划；随后用 aios_execute 以 execute_all=true、approve_all=true、confirmed=true、commit=true 串行执行完整闭环，过程中用 aios_inspect 可观测与续跑，失败触发对应 compensate 回滚。
```

> 占位符 `{WORK_ORDER_NO}` / `{EQUIPMENT_NAME}` / `{EQUIPMENT_MODEL}` / `{FAULT_DESC}` 由前端按当前工单上下文自动填充。步骤数、依赖、写步骤审批门禁、compensate 回滚、aios_inspect 续跑等细节均由天工依据 AGENT_TOOL_ALLOWLISTS 与 AIOS_ACTION_REGISTRY 自主推断，无需在提示词中固化。
