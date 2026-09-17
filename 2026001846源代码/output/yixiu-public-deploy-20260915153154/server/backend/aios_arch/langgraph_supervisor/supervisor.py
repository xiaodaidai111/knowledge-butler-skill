"""Supervisor 状态结构 + 节点函数。

State 字段对齐 aios_runtime 的 plan 结构，确保对前端契约零破坏：
- run_id / plan / artifacts / approvals / actor / context / trace_id / decisions
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aios_arch.langgraph_supervisor.graph import StateGraph, CompiledGraph
import aios_arch.trace as trace
import aios_arch.opa_guard as opa
import aios_arch.memory_layer as memory

logger = logging.getLogger("aios_arch.langgraph_supervisor.nodes")


def _new_run_id() -> str:
    return f"run-{uuid.uuid4().hex[:16]}"


def _ensure_actor(state: dict) -> dict:
    actor = state.get("actor") or {
        "user_id": "tiangong-supervisor", "role": "admin",
    }
    state["actor"] = actor
    return actor


def _ensure_trace(state: dict, name: str = "aios_supervisor_run") -> str:
    trace_id = state.get("trace_id")
    if not trace_id:
        trace_id = trace.start_trace(
            name=name,
            user_id=_ensure_actor(state).get("user_id", ""),
            session_id=state.get("session_id", ""),
            metadata={"run_id": state.get("run_id", "")},
            input_data=state.get("goal"),
        )
        state["trace_id"] = trace_id
    return trace_id


def start_node(state: dict) -> dict:
    """入口节点：初始化 run_id、trace、actor、approvals。"""
    if not state.get("run_id"):
        state["run_id"] = _new_run_id()
    _ensure_trace(state)
    state.setdefault("approvals", {})
    state.setdefault("artifacts", {})
    state.setdefault("decisions", [])
    state.setdefault("completed_steps", [])
    logger.info("supervisor start run=%s trace=%s", state["run_id"], state.get("trace_id"))
    return {"run_id": state["run_id"], "trace_id": state["trace_id"],
            "approvals": state["approvals"], "artifacts": state["artifacts"]}


def build_plan_node(state: dict) -> dict:
    """天工 aios_plan：根据 goal 调用 aios_plan 工具生成结构化计划。"""
    obs_id = trace.start_observation(
        state["trace_id"], name="build_plan", type_="span",
        input_data={"goal": state.get("goal")}, model="tiangong",
    )
    plan = state.get("plan") or {}
    if not plan.get("steps"):
        try:
            from aios_arch.mcp_gateway import call_tool
            result = call_tool("aios_plan", {
                "goal": state.get("goal", ""),
                "mode": state.get("mode", "auto"),
                "task_id": state.get("task_id", ""),
            })
            output = ""
            for c in result.get("content", []):
                if c.get("type") == "text":
                    output += c.get("text", "")
            plan = (result.get("metadata") or {}).get("plan") or {"steps": []}
            if not plan.get("steps") and output:
                plan["steps"] = [{"key": f"step_{i}", "title": line}
                                 for i, line in enumerate(output.splitlines()) if line]
            state["plan"] = plan
        except Exception as exc:  # noqa: BLE001
            logger.warning("build_plan fallback: %s", exc)
            plan = state.get("plan") or {"steps": []}
            state["plan"] = plan
    trace.end_observation(obs_id, status="completed",
                          output_data={"steps": len(plan.get("steps", []))},
                          metadata={"plan_keys": [s.get("key") for s in plan.get("steps", [])]})
    return {"plan": plan}


def _run_step(state: dict, step: dict) -> dict:
    """执行单个 plan step：走 MCP Gateway 调用工具 + OPA 拦截 write。"""
    step_key = str(step.get("key") or step.get("action") or "")
    action = step.get("action") or step_key
    requires_approval = bool(step.get("requires_approval"))
    kind = "write" if requires_approval else "read"
    artifact_key = step_key or action
    trace_id = state["trace_id"]

    obs_id = trace.start_observation(
        trace_id, name=f"step:{step_key}", type_="span",
        parent_id=state.get("current_obs_id"),
        input_data=step, model=step.get("agent", {}).get("id", "tiangong"),
    )

    actor = state["actor"]
    decision = opa.evaluate(
        action=f"aios.execute.{action}",
        resource=f"step:{step_key}",
        payload=step,
        actor=actor,
        context={"kind": kind, "approve_all": state.get("approve_all", False),
                 "approved": state.get("approvals", {}).get(step_key, False)},
        trace_id=trace_id,
    )
    state["decisions"].append({"step": step_key, "decision": decision})
    if decision["decision"] == "deny":
        trace.end_observation(obs_id, status="denied",
                              output_data=decision,
                              metadata={"opa": decision["decision_id"]},
                              level="WARNING")
        return {artifact_key: {"status": "denied", "reason": decision["reason"]}}

    tool_name = step.get("capability") or step.get("tool") or action
    try:
        from aios_arch.mcp_gateway import call_tool
        result = call_tool(tool_name, step.get("args") or step.get("arguments") or {})
    except Exception as exc:  # noqa: BLE001
        trace.end_observation(obs_id, status="failed", output_data={"error": str(exc)},
                              level="ERROR")
        return {artifact_key: {"status": "failed", "error": str(exc)}}

    artifact = {
        "status": "failed" if result.get("isError") else "completed",
        "tool": result.get("tool", tool_name),
        "content": result.get("content", []),
        "metadata": result.get("metadata", {}),
    }
    state["completed_steps"].append(step_key)
    state["approvals"][step_key] = True
    trace.end_observation(obs_id, status="completed",
                          output_data=artifact, metadata={"tool": tool_name})
    return {artifact_key: artifact}


def execute_steps_node(state: dict) -> dict:
    """批量执行所有未完成步骤（execute_all）。"""
    plan = state.get("plan") or {}
    steps = plan.get("steps", [])
    completed = set(state.get("completed_steps", []))
    for step in steps:
        key = str(step.get("key") or step.get("action") or "")
        if key in completed:
            continue
        patch = _run_step(state, step)
        state["artifacts"].update(patch)
    state["plan"]["steps"] = [
        {**s, "state": "done" if str(s.get("key") or s.get("action") or "") in state.get("completed_steps", []) else s.get("state", "pending")}
        for s in steps
    ]
    return {"artifacts": state["artifacts"], "plan": state["plan"],
            "completed_steps": state["completed_steps"]}


def memory_node(state: dict) -> dict:
    """把关键产物沉淀到 Mem0 风格记忆层。"""
    goal = state.get("goal", "")
    artifacts = state.get("artifacts", {})
    content = f"goal={goal}; artifacts={list(artifacts.keys())}; completed={state.get('completed_steps', [])}"
    mem_id = memory.add(
        user_id=state["actor"]["user_id"],
        agent_id="tiangong",
        content=content,
        metadata={"run_id": state.get("run_id"), "trace_id": state.get("trace_id")},
    )
    return {"memory_id": mem_id}


def finalize_node(state: dict) -> dict:
    """收尾：结束 trace + 汇总报告。"""
    trace.end_trace(
        state.get("trace_id"),
        status="completed",
        output_data={
            "run_id": state.get("run_id"),
            "completed_steps": state.get("completed_steps", []),
            "artifacts": list((state.get("artifacts") or {}).keys()),
        },
    )
    return {"final_report": {
        "run_id": state.get("run_id"),
        "trace_id": state.get("trace_id"),
        "completed": state.get("completed_steps", []),
        "artifacts": state.get("artifacts", {}),
        "memory_id": state.get("memory_id"),
    }}


def build_supervisor_graph() -> CompiledGraph:
    """构建天工 Supervisor 的 StateGraph：
        START -> start -> build_plan -> execute_steps -> memory -> finalize -> END
    """
    g = StateGraph()
    g.add_node("start", start_node)
    g.add_node("build_plan", build_plan_node)
    g.add_node("execute_steps", execute_steps_node)
    g.add_node("memory", memory_node)
    g.add_node("finalize", finalize_node)
    g.set_entry_point("start")
    g.add_edge("start", "build_plan")
    g.add_edge("build_plan", "execute_steps")
    g.add_edge("execute_steps", "memory")
    g.add_edge("memory", "finalize")
    g.set_finish_point("finalize")
    return g.compile()


def run_supervisor(goal: str, mode: str = "auto", task_id: str = "",
                   execute_all: bool = True, approve_all: bool = True,
                   actor: Optional[dict] = None,
                   session_id: str = "") -> dict:
    """对外入口：跑完整 Supervisor 闭环。"""
    graph = build_supervisor_graph()
    initial = {
        "goal": goal,
        "mode": mode,
        "task_id": task_id,
        "execute_all": execute_all,
        "approve_all": approve_all,
        "actor": actor or {"user_id": "tiangong-supervisor", "role": "admin"},
        "session_id": session_id,
    }
    return graph.invoke(initial, max_steps=128)
