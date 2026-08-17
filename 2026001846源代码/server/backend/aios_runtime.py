"""AIOS agent contracts and workflow state machine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


AIOS_TECH_STACK: dict[str, dict[str, str]] = {
    "orchestration": {
        "name": "LangGraph",
        "role": "多智能体编排与状态图",
        "effect": "把用户目标拆成可追踪节点，管理依赖、分支、重试、恢复和人工审批。",
    },
    "tools": {
        "name": "MCP",
        "role": "统一工具协议",
        "effect": "把任务、知识库、文件、图谱、联系人、审批、报告等系统能力暴露给 Agent 调用。",
    },
    "sandbox": {
        "name": "E2B",
        "role": "安全执行沙箱",
        "effect": "用于文件解析、脚本验证、临时计算和高风险工具调用隔离，避免影响业务主环境。",
    },
    "memory": {
        "name": "Postgres + pgvector",
        "role": "长期记忆与向量检索",
        "effect": "保存会话、用户偏好、设备状态、检修经验、知识切片和跨模态向量索引。",
    },
    "entry": {
        "name": "FastAPI",
        "role": "AIOS 统一入口",
        "effect": "承载 Agent、Workflow、Trace、Memory、RAG、MCP 和多渠道 API。",
    },
    "observability": {
        "name": "LangSmith",
        "role": "运行观测与 Trace",
        "effect": "记录模型调用、工具调用、智能体协作链路、耗时、错误和人工审批节点。",
    },
}


TIANGONG_OPERATION_PROMPT = """
你是“天工”，一修设备检修系统的 AIOS 总控智能体。你运行在 LangGraph（编排）+ MCP（工具）+ E2B（沙箱）+ Postgres/pgvector（记忆）+ FastAPI（入口）+ LangSmith（观测）的智能体技术栈上。

你的目标不是只回答问题，而是像系统里的执行代理一样，根据用户自然语言指令，规划并操作一修 Web 工作台的所有页面：首页、智能检索、检修任务、知识库、个人中心，以及各页面中的弹窗、抽屉、筛选、上传、详情、审核、复检、联系人交流和悬浮智能体。

收到复杂任务时，必须先给出不少于 10 步的可视化执行计划。每一步都要包含：步骤编号、目标页面、负责智能体、要调用的工具或页面动作、输入数据、预期结果、是否需要人工确认。计划必须按可执行顺序组织，并标明依赖关系。

多智能体分工规则：
1. 天工负责理解目标、拆解步骤、选择页面、调度其他智能体、汇总结果。
2. 观微负责多模态检索、图片/文档/型号/故障码分析、RAG 资料召回。
3. 执矩负责检修任务、SOP、作业步骤、安全确认、工单流转。
4. 博闻负责知识库、文件管理、知识图谱、知识沉淀、版本和审核。
5. 和鸣负责联系人交流、任务群聊、专家支援、消息总结和协作纪要。
6. 明鉴负责复检评估、质量评分、风险核查、报告验收和闭环确认。

执行策略：
- 先感知系统状态，再规划；先读数据，再写数据。
- 优先调用 MCP 工具读取真实任务、文件、知识、联系人、审批和 Trace。
- 需要文件解析、代码计算、批量整理或不可信输入处理时，先放入 E2B 沙箱。
- 需要上下文延续时，读取 Postgres/pgvector 中的会话记忆、设备记忆和知识向量。
- 需要观察运行过程时，向 LangSmith Trace 写入模型调用、工具调用、Agent 调用、审批和错误。
- 涉及创建任务、更新知识库、提交复检、删除文件、生成正式报告等高风险动作时，必须触发 Human-in-the-loop：展示“拒绝 / 批准”，批准后再继续。
- 如果用户要求“让我看到过程”，输出可视化 UI_PLAN，让前端显示页面跳转、输入、点击、筛选、打开详情、等待结果、调用智能体和完成状态。
- 如果某一步失败，说明失败原因，给出补救步骤，并允许从失败步骤继续执行。

可视化 UI_PLAN 输出要求：
在需要操作页面时，回复末尾输出 [UI_PLAN] JSON。JSON 至少包含 10 个 steps，每个 step 包含 action、page、agent、target、input、reason、expected、requiresApproval。动作可使用 navigate、search、filter、openPanel、upload、preview、invokeAgent、createTask、openKnowledgeGraph、openChat、summarize、approve、report、finish。

回答风格：
面向检修人员，不展示密钥、端口、接口路径、数据库连接串或开发日志。用清晰自然的中文说明“我准备做什么、正在做什么、做成了什么、还需要你确认什么”。
""".strip()


AGENT_OUTPUT_SCHEMAS: dict[str, dict[str, str]] = {
    "tiangong": {"summary": "string", "plan": "object", "next_action": "object"},
    "guanwei": {"summary": "string", "references": "array", "suggestion": "string"},
    "zhiju": {"summary": "string", "sop": "array", "safety": "array", "recommended_status": "string"},
    "bowen": {"summary": "string", "references": "array", "knowledge_candidate": "object"},
    "heming": {"summary": "string", "contacts": "array", "today": "object"},
    "mingjian": {"summary": "string", "score": "number", "checklist": "array", "recommendation": "string"},
}


AGENT_PROMPTS: dict[str, str] = {
    "tiangong": TIANGONG_OPERATION_PROMPT,
    "guanwei": "你是检索智能体，只输出证据、引用、相似案例和不确定性，不直接修改业务数据。",
    "zhiju": "你是作业智能体，只输出 SOP、工具备件、安全确认和工单状态建议。",
    "bowen": "你是知识智能体，只生成待审核知识候选，不绕过人工审核入库。",
    "heming": "你是协作智能体，只输出联系人建议、协作摘要和消息草稿。",
    "mingjian": "你是核查智能体，只输出质量评分、核查清单、阻断项和返工建议。",
}


AGENT_TOOL_ALLOWLISTS: dict[str, list[str]] = {
    "tiangong": [
        "aios_platform", "aios_plan", "aios_execute", "aios_inspect", "aios_approval",
        "agent_dispatch", "agent_status", "agent_invoke", "system_overview",
        "maintenance_task", "knowledge_search", "knowledge_graph", "database_status",
    ],
    "guanwei": ["knowledge_search", "rag_query", "file_parse", "vision_analyze"],
    "zhiju": ["sop_generate", "safety_check", "task_update"],
    "bowen": ["knowledge_link", "knowledge_candidate_create", "version_read"],
    "heming": ["contacts_read", "conversation_message_draft", "support_request_draft"],
    "mingjian": ["audit", "recheck", "quality_score", "report_verify"],
}

AIOS_ACTION_REGISTRY: dict[str, dict[str, Any]] = {
    "sense_overview": {
        "capability": "system_overview",
        "agent": "tiangong",
        "kind": "read",
        "requires_approval": False,
        "description": "读取任务、设备、联系人和知识库概览，锁定当前目标。",
    },
    "retrieve_knowledge": {
        "capability": "knowledge_search",
        "agent": "guanwei",
        "kind": "read",
        "requires_approval": False,
        "description": "检索维修手册、SOP、历史案例和安全规范。",
    },
    "diagnose_fault": {
        "capability": "rag_query",
        "agent": "guanwei",
        "kind": "read",
        "requires_approval": False,
        "description": "结合任务上下文和知识命中生成故障判断依据。",
    },
    "orchestrate_task": {
        "capability": "task_update",
        "agent": "zhiju",
        "kind": "write",
        "requires_approval": True,
        "description": "编排可执行 SOP、工具备件、安全确认和任务状态建议。",
    },
    "coordinate_team": {
        "capability": "conversation_message_draft",
        "agent": "heming",
        "kind": "write",
        "requires_approval": True,
        "description": "推荐协作人员并生成/沉淀任务会话消息。",
    },
    "prepare_recheck": {
        "capability": "recheck",
        "agent": "mingjian",
        "kind": "read",
        "requires_approval": False,
        "description": "生成复检验收清单、质量门禁和返工规则。",
    },
    "record_memory": {
        "capability": "task_memory",
        "agent": "tiangong",
        "kind": "write",
        "requires_approval": True,
        "description": "把本次处理的关键判断沉淀到任务记忆。",
    },
    "archive_knowledge": {
        "capability": "knowledge_candidate_create",
        "agent": "bowen",
        "kind": "write",
        "requires_approval": True,
        "description": "生成待审核知识候选，等待人工确认入库。",
    },
    "finalize_report": {
        "capability": "report_verify",
        "agent": "mingjian",
        "kind": "read",
        "requires_approval": False,
        "description": "汇总执行产物、下一步和待审批事项。",
    },
}


FINAL_STATES = {"done", "failed", "compensated", "skipped"}
EXECUTABLE_STATES = {"pending", "retrying", "blocked", "waiting_approval"}


@dataclass(frozen=True)
class AgentSpec:
    id: str
    prompt: str
    tool_allowlist: list[str]
    output_schema: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def agent_spec(agent_id: str) -> AgentSpec:
    key = str(agent_id or "tiangong").strip()
    return AgentSpec(
        id=key,
        prompt=AGENT_PROMPTS.get(key, AGENT_PROMPTS["tiangong"]),
        tool_allowlist=AGENT_TOOL_ALLOWLISTS.get(key, AGENT_TOOL_ALLOWLISTS["tiangong"]),
        output_schema=AGENT_OUTPUT_SCHEMAS.get(key, AGENT_OUTPUT_SCHEMAS["tiangong"]),
    )


def enrich_agent(agent: dict[str, Any]) -> dict[str, Any]:
    spec = agent_spec(agent.get("id", "tiangong")).to_dict()
    return {**agent, "prompt": spec["prompt"], "tool_allowlist": spec["tool_allowlist"], "output_schema": spec["output_schema"]}


def build_state_machine(steps: list[dict[str, Any]], mode: str = "auto") -> dict[str, Any]:
    nodes = []
    previous_key = ""
    for index, step in enumerate(steps):
        key = str(step.get("key") or f"step_{index + 1}")
        deps = [] if not previous_key else [previous_key]
        if mode == "review" and key == "review":
            deps = ["retrieve"]
        if mode == "knowledge" and key == "archive":
            deps = ["retrieve", "review"]
        node = {
            "key": key,
            "state": step.get("state") or step.get("status") or "pending",
            "depends_on": step.get("depends_on") or deps,
            "attempts": int(step.get("attempts") or 0),
            "max_retries": int(step.get("max_retries") or 2),
            "requires_approval": bool(step.get("requires_approval", AIOS_ACTION_REGISTRY.get(step.get("action", ""), {}).get("requires_approval", key in {"operate", "collaborate", "archive"}))),
            "approved": bool(step.get("approved", False)),
            "compensation": step.get("compensation") or {
                "action": f"compensate_{key}",
                "status": "not_started",
            },
            "last_error": step.get("last_error") or "",
            "updated_at": step.get("updated_at") or now(),
        }
        nodes.append(node)
        previous_key = key
    return {
        "version": "2026-08-10",
        "state": _workflow_state(nodes),
        "supports": ["depends_on", "failed", "retry", "paused", "approval", "compensation"],
        "nodes": nodes,
    }


def attach_state_machine(plan: dict[str, Any]) -> dict[str, Any]:
    steps = plan.get("steps") or []
    machine = plan.get("state_machine") or build_state_machine(steps, plan.get("mode", "auto"))
    step_by_key = {step.get("key"): step for step in steps}
    for node in machine.get("nodes", []):
        step = step_by_key.get(node.get("key")) or {}
        if "max_retries" in step:
            node["max_retries"] = int(step.get("max_retries") or 0)
        if "requires_approval" in step:
            node["requires_approval"] = bool(step.get("requires_approval"))
        if "approved" in step:
            node["approved"] = bool(step.get("approved"))
    node_by_key = {node["key"]: node for node in machine.get("nodes", [])}
    enriched_steps = []
    for step in steps:
        node = node_by_key.get(step.get("key"), {})
        agent = step.get("agent") or {}
        enriched_steps.append({
            **step,
            "agent": enrich_agent(agent),
            "state": node.get("state", step.get("status", "pending")),
            "depends_on": node.get("depends_on", []),
            "attempts": node.get("attempts", 0),
            "max_retries": node.get("max_retries", 2),
            "requires_approval": node.get("requires_approval", False),
            "approved": node.get("approved", False),
            "compensation": node.get("compensation", {}),
        })
    plan["steps"] = enriched_steps
    plan["state_machine"] = build_state_machine(enriched_steps, plan.get("mode", "auto"))
    plan["workflow_state"] = plan["state_machine"]["state"]
    return plan


def transition_step(
    plan: dict[str, Any],
    step_key: str,
    event: str,
    error: str = "",
    approvals: dict[str, bool] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    approvals = approvals or {}
    plan = attach_state_machine(plan)
    machine = plan["state_machine"]
    nodes = {node["key"]: node for node in machine["nodes"]}
    node = nodes.get(step_key)
    if not node:
        raise ValueError(f"unknown step: {step_key}")

    if event == "pause":
        node["state"] = "paused"
    elif event == "approve":
        node["approved"] = True
        if node["state"] == "waiting_approval":
            node["state"] = "pending"
    elif event == "fail":
        if node.get("state") != "running":
            node["attempts"] += 1
        node["last_error"] = error or "step failed"
        node["state"] = "retrying" if node["attempts"] <= node["max_retries"] else "failed"
    elif event == "compensate":
        node["state"] = "compensated"
        node["compensation"] = {**node.get("compensation", {}), "status": "done", "updated_at": now()}
    elif event == "execute":
        blocked = _first_blocker(node, nodes, approvals)
        if blocked:
            node["state"] = blocked["state"]
            node["last_error"] = blocked["reason"]
        else:
            node["attempts"] += 1
            node["state"] = "running"
    elif event == "complete":
        node["state"] = "done"
        node["last_error"] = ""
    else:
        raise ValueError(f"unsupported transition event: {event}")

    node["updated_at"] = now()
    _sync_machine_to_steps(plan, machine)
    return plan, node


def next_executable_steps(plan: dict[str, Any], approvals: dict[str, bool] | None = None) -> list[dict[str, Any]]:
    approvals = approvals or {}
    plan = attach_state_machine(plan)
    nodes = {node["key"]: node for node in plan["state_machine"]["nodes"]}
    ready = []
    for step in plan.get("steps", []):
        node = nodes.get(step.get("key"), {})
        if node.get("state") not in EXECUTABLE_STATES:
            continue
        if _first_blocker(node, nodes, approvals):
            continue
        ready.append(step)
    return ready


def _first_blocker(node: dict[str, Any], nodes: dict[str, dict[str, Any]], approvals: dict[str, bool]) -> dict[str, str] | None:
    for dep in node.get("depends_on", []):
        if nodes.get(dep, {}).get("state") != "done":
            return {"state": "blocked", "reason": f"dependency not done: {dep}"}
    if node.get("requires_approval") and not (node.get("approved") or approvals.get(node["key"])):
        return {"state": "waiting_approval", "reason": "approval required"}
    return None


def _sync_machine_to_steps(plan: dict[str, Any], machine: dict[str, Any]) -> None:
    node_by_key = {node["key"]: node for node in machine["nodes"]}
    for step in plan.get("steps", []):
        node = node_by_key.get(step.get("key"))
        if not node:
            continue
        step["state"] = node["state"]
        step["status"] = "done" if node["state"] == "done" else node["state"]
        step["attempts"] = node["attempts"]
        step["last_error"] = node.get("last_error", "")
        step["approved"] = node.get("approved", False)
    machine["state"] = _workflow_state(machine["nodes"])
    plan["workflow_state"] = machine["state"]


def _workflow_state(nodes: list[dict[str, Any]]) -> str:
    states = {node.get("state", "pending") for node in nodes}
    if states and states <= {"done"}:
        return "completed"
    if "failed" in states:
        return "failed"
    if "paused" in states:
        return "paused"
    if "waiting_approval" in states:
        return "waiting_approval"
    if "running" in states or "retrying" in states:
        return "running"
    if "blocked" in states:
        return "blocked"
    return "planned"


# ---------------------------------------------------------------------------
# LangGraph Supervisor 委托入口
# 新架构（aios_arch.langgraph_supervisor）按 StateGraph + conditional edges 编排，
# 经 MCP Gateway 调用工具、OPA Guard 拦截 write、Memory Layer 沉淀记忆、Trace 全链路。
# 本函数对外保持稳定契约：返回 {run_id, trace_id, plan, artifacts, decisions, final_report}。
# ---------------------------------------------------------------------------
def supervisor_execute(goal: str, mode: str = "auto", task_id: str = "",
                       execute_all: bool = True, approve_all: bool = True,
                       actor: dict[str, Any] | None = None,
                       session_id: str = "") -> dict[str, Any]:
    """天工 Supervisor 长任务闭环入口（不破坏老状态机语义）。"""
    try:
        from aios_arch.langgraph_supervisor import run_supervisor
    except Exception as exc:  # noqa: BLE001
        return {"run_id": "", "trace_id": "", "error": f"supervisor_unavailable: {exc}",
                "artifacts": {}, "decisions": [], "final_report": {}}
    return run_supervisor(
        goal=goal, mode=mode, task_id=task_id,
        execute_all=execute_all, approve_all=approve_all,
        actor=actor, session_id=session_id,
    )
