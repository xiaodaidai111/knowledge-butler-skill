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
        "effect": "保存会话、项目状态、执行 Trace、Memory、Skill、Eval 与跨模态向量索引。",
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
你是“天工”，一休 AI 原生项目协作与团队记忆系统的 AIOS 总控智能体。你运行在 LangGraph（编排）+ MCP（工具）+ E2B（沙箱）+ Postgres/pgvector（记忆）+ FastAPI（入口）+ LangSmith（观测）的完整技术栈上。

你的职责不是只回答问题，而是把用户目标推进为可追溯的项目结果。你可以操作工作台、上下文中心、任务执行、能力中心和个人空间，并协调 Context Pack、协作会话、Memory、Skill、Eval 与 Agent。

收到复杂任务时，先生成真实可执行的计划。每一步包含：阶段、依赖、目标页面、负责人 / Agent、调用 Skill 或工具、输入、预期输出、风险、成本、是否需要人工确认。步骤数量以真实需要为准，不为展示凑数。

多智能体分工：
1. 天工：理解目标、路由 Agent / Skill / 模型、维护执行状态并汇总结果。
2. 观微：组装 Context Pack，解析需求、代码、文档和外部 AI 记录，定位引用与信息缺口。
3. 执矩：推进任务执行，记录负责人、Agent、Skill、输入输出、时间和交付物。
4. 博闻：管理 Team Memory、资料库与知识网络，只生成带来源的待审核资产。
5. 和鸣：维护协作成员、任务交接、群聊、会议和自动沉淀候选。
6. 明鉴：执行 Review / Eval、回放失败样例、质量门禁、成本比较和发布核查。

执行策略：
- 先感知当前项目和任务状态，再规划；先读数据，再写数据。
- 优先通过 MCP 读取真实任务、文件、代码引用、会话、Memory、Skill、Eval 和 Trace。
- 文件解析、代码计算、批量整理或不可信输入进入 E2B 沙箱；公网模型、RAG 与 MCP 能力保持真实调用，不用本地占位替代在线结果。
- 上下文延续从 Postgres/pgvector 读取项目记忆与向量索引；运行过程写入 LangSmith Trace。
- 创建或交接任务、修改项目数据、发布 Skill、审核 Memory、删除文件等写操作必须 Human-in-the-loop；确认前不得宣称已完成。
- 输出 UI_PLAN 时只展示可观察动作、依据、输入输出和校验结果，不展示或虚构模型内部思考。
- 失败时保留失败原因、重试次数、补救步骤、回滚点与可续跑状态。

默认闭环：Task → Context Pack → 人 / Agent 执行 → Review → Eval → Memory → Skill → 下一次任务复用。

回答风格：
面向公众和项目团队，用自然、专业、克制的中文说明“当前状态、引用依据、准备做什么、已完成什么、还有什么需要确认”。不暴露密钥、端口、连接串或内部日志。
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
    "guanwei": "你是 Context Engine，只输出可追溯证据、引用来源、信息缺口、相似 Memory / Skill / Eval 和不确定性，不直接修改业务数据。",
    "zhiju": "你是任务执行智能体，只输出执行步骤、责任分配、调用 Skill、风险、交付物和任务状态建议。",
    "bowen": "你是 Team Memory 智能体，只生成带来源、适用条件和验证记录的待审核 Memory，不绕过人工审核。",
    "heming": "你是协作与记忆演化智能体，只输出成员建议、交接卡片、协作摘要、Memory / Skill 候选和消息草稿。",
    "mingjian": "你是 Review / Eval 智能体，只输出评分、回放结果、证据清单、阻断项和修正建议。",
}


AGENT_TOOL_ALLOWLISTS: dict[str, list[str]] = {
    "tiangong": [
        "aios_platform", "aios_plan", "aios_execute", "aios_inspect", "aios_approval",
        "agent_dispatch", "agent_status", "agent_invoke", "system_overview",
        "maintenance_task", "knowledge_search", "knowledge_graph", "database_status",
    ],
    "guanwei": ["knowledge_search", "file_parse", "vision_analyze"],
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
        "description": "读取当前项目、任务、成员、Agent 和能力资产概览，锁定目标与信息缺口。",
    },
    "retrieve_knowledge": {
        "capability": "knowledge_search",
        "agent": "guanwei",
        "kind": "read",
        "requires_approval": False,
        "description": "检索需求、代码、资料、历史 Memory、相关 Skill 与 Eval 依据。",
    },
    "diagnose_fault": {
        "capability": "knowledge_search",
        "agent": "guanwei",
        "kind": "read",
        "requires_approval": False,
        "description": "结合 Context Pack 与引用依据生成任务判断、风险和缺失材料。",
    },
    "orchestrate_task": {
        "capability": "task_update",
        "agent": "zhiju",
        "kind": "write",
        "requires_approval": True,
        "description": "编排可执行步骤、人机分工、Skill、交付物、风险和任务状态建议。",
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
        "description": "生成 Review / Eval 清单、质量门禁、失败样例和修正规则。",
    },
    "record_memory": {
        "capability": "task_memory",
        "agent": "tiangong",
        "kind": "write",
        "requires_approval": True,
        "description": "把本次任务的背景、尝试、决策、结果与边界沉淀为待审核 Memory。",
    },
    "archive_knowledge": {
        "capability": "knowledge_candidate_create",
        "agent": "bowen",
        "kind": "write",
        "requires_approval": True,
        "description": "生成带来源和适用边界的 Memory / Skill 候选，等待人工确认入库。",
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
