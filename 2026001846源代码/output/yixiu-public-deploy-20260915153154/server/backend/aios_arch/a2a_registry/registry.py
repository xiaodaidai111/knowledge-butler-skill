"""A2A Registry：AgentCard 注册 + message/send 协议。

不接真 A2A server，本地实现 A2A 协议骨架：
- AgentCard：name/url/description/skills/defaultInputModes/defaultOutputModes/version
- message/send：把 TaskMessage 路由给子 agent 执行（通过 miniclaw system_tools.AgentInvokeTool）
- message/get / tasks/get：拉取任务状态
- 子 agent 发现：六大智能体（tiangong/guanwei/zhiju/bowen/heming/mingjian）默认注册

A2A 协议核心字段对齐 a2a-python sdk：
- JSON-RPC 2.0 over HTTP
- message/send params: {message: Message, metadata: {...}}
- Message: {role, parts: [{kind: "text", text}]}, messageId, taskId, contextId
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("aios_arch.a2a_registry")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
A2A_DB_PATH = DATA_DIR / "aios_a2a.db"

DEFAULT_AGENTS = [
    {"id": "tiangong", "name": "天工", "description": "AIOS 综合智能中枢，统筹其他智能体协作",
     "skills": [{"name": "aios_plan", "description": "AIOS 长任务规划"},
                {"name": "aios_execute", "description": "AIOS 计划执行"},
                {"name": "system_overview", "description": "系统概览"}],
     "url": "a2a://tiangong", "version": "0.1.0"},
    {"id": "guanwei", "name": "观微", "description": "智能检索器灵，召回历史案例与 RAG 故障判断",
     "skills": [{"name": "knowledge_search", "description": "知识检索"},
                {"name": "rag_query", "description": "RAG 向量检索"},
                {"name": "file_parse", "description": "文件解析切片"},
                {"name": "vision_analyze", "description": "视觉分析"}],
     "url": "a2a://guanwei", "version": "0.1.0"},
    {"id": "zhiju", "name": "执矩", "description": "检修作业器灵，编排 SOP 并推进工单流转",
     "skills": [{"name": "sop_generate", "description": "标准作业步骤生成"},
                {"name": "task_update", "description": "工单状态推进"}],
     "url": "a2a://zhiju", "version": "0.1.0"},
    {"id": "bowen", "name": "博闻", "description": "知识管理器灵，沉淀待审核知识候选",
     "skills": [{"name": "knowledge_candidate_create", "description": "知识候选生成"},
                {"name": "file_parse", "description": "知识文件切片入库"},
                {"name": "rag_query", "description": "知识召回验证"}],
     "url": "a2a://bowen", "version": "0.1.0"},
    {"id": "heming", "name": "和鸣", "description": "协作调度器灵，协调人员并发起专家支援",
     "skills": [{"name": "contacts_read", "description": "联系人推荐"},
                {"name": "conversation_message_draft", "description": "协作消息草稿"},
                {"name": "support_request_draft", "description": "专家支援请求"}],
     "url": "a2a://heming", "version": "0.1.0"},
    {"id": "mingjian", "name": "明鉴", "description": "复检核查器灵，质量评分与验收清单",
     "skills": [{"name": "recheck", "description": "复检清单"},
                {"name": "quality_score", "description": "质量评分"},
                {"name": "report_verify", "description": "报告核验"}],
     "url": "a2a://mingjian", "version": "0.1.0"},
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS a2a_agents (
  id TEXT PRIMARY KEY,
  card_json TEXT NOT NULL,
  status TEXT DEFAULT 'online',
  last_heartbeat TEXT,
  registered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS a2a_tasks (
  id TEXT PRIMARY KEY,
  context_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  status TEXT DEFAULT 'submitted',
  history_json TEXT DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS a2a_messages (
  id TEXT PRIMARY KEY,
  task_id TEXT,
  context_id TEXT NOT NULL,
  from_agent TEXT,
  to_agent TEXT NOT NULL,
  role TEXT DEFAULT 'user',
  parts_json TEXT DEFAULT '[]',
  kind TEXT DEFAULT 'text',
  reply_to TEXT,
  status TEXT DEFAULT 'pending',
  response_json TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_task ON a2a_messages(task_id);
CREATE INDEX IF NOT EXISTS idx_msg_to ON a2a_messages(to_agent);
"""


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(A2A_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _seed_default_agents(conn: sqlite3.Connection) -> None:
    for agent in DEFAULT_AGENTS:
        existing = conn.execute("SELECT id FROM a2a_agents WHERE id=?", (agent["id"],)).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO a2a_agents VALUES (?, ?, ?, ?, ?)",
            (agent["id"], json.dumps(agent, ensure_ascii=False),
             "online", _now(), _now()),
        )


def register_agent(card: dict) -> str:
    aid = str(card.get("id") or card.get("name") or f"agent-{uuid.uuid4().hex[:8]}")
    card = {**card, "id": aid, "version": card.get("version", "0.1.0")}
    with _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO a2a_agents VALUES (?, ?, ?, ?, ?)",
            (aid, json.dumps(card, ensure_ascii=False), "online", _now(), _now()),
        )
    logger.info("a2a agent registered: %s", aid)
    return aid


def list_agents() -> list[dict]:
    with _db() as conn:
        _seed_default_agents(conn)
        rows = conn.execute("SELECT * FROM a2a_agents").fetchall()
        return [json.loads(r["card_json"]) for r in rows]


def get_agent(agent_id: str) -> Optional[dict]:
    with _db() as conn:
        _seed_default_agents(conn)
        row = conn.execute("SELECT * FROM a2a_agents WHERE id=?", (agent_id,)).fetchone()
        return json.loads(row["card_json"]) if row else None


def _invoke_subagent(agent_id: str, goal: str, task_id: str = "") -> dict:
    """调用 AgentInvokeTool 让子 agent 真正执行任务。"""
    try:
        from miniclaw.builtins.system_tools import AgentInvokeTool
        tool = AgentInvokeTool()
        result = tool.execute(agent_id=agent_id, goal=goal, task_id=task_id, commit=True)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "metadata": result.metadata,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("a2a subagent invoke fallback: %s", exc)
        return {"success": False, "output": "", "error": str(exc), "metadata": {}}


def send_message(from_agent: str, to_agent: str, text: str,
                 context_id: str = "", task_id: Optional[str] = None,
                 reply_to: Optional[str] = None, kind: str = "text") -> dict:
    """A2A message/send：路由消息到目标子 agent 并触发执行。"""
    if not context_id:
        context_id = f"ctx-{uuid.uuid4().hex[:12]}"
    if not task_id:
        task_id = f"task-{uuid.uuid4().hex[:12]}"
    msg_id = f"msg-{uuid.uuid4().hex[:16]}"
    with _db() as conn:
        _seed_default_agents(conn)
        conn.execute(
            "INSERT INTO a2a_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (msg_id, task_id, context_id, from_agent, to_agent, "user",
             json.dumps([{"kind": kind, "text": text}], ensure_ascii=False),
             kind, reply_to, "pending", None, _now()),
        )
        existing_task = conn.execute(
            "SELECT id FROM a2a_tasks WHERE id=?", (task_id,),
        ).fetchone()
        if not existing_task:
            conn.execute(
                "INSERT INTO a2a_tasks VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, context_id, to_agent, "working", "[]", _now(), _now()),
            )

    invoke_result = _invoke_subagent(to_agent, text, task_id or "")
    response_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
    response_parts = [{
        "kind": "text",
        "text": invoke_result.get("output") or invoke_result.get("error") or "(no output)",
    }]
    final_status = "completed" if invoke_result.get("success") else "failed"
    with _db() as conn:
        conn.execute(
            "INSERT INTO a2a_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (response_msg_id, task_id, context_id, to_agent, from_agent, "agent",
             json.dumps(response_parts, ensure_ascii=False), "text",
             msg_id, final_status,
             json.dumps(invoke_result, ensure_ascii=False), _now()),
        )
        conn.execute(
            "UPDATE a2a_tasks SET status=?, history_json=?, updated_at=? WHERE id=?",
            (final_status,
             json.dumps([{"role": "user", "text": text},
                        {"role": "agent", "text": response_parts[0]["text"]}],
                       ensure_ascii=False),
             _now(), task_id),
        )
        conn.execute(
            "UPDATE a2a_messages SET status=?, response_json=? WHERE id=?",
            (final_status, json.dumps(invoke_result, ensure_ascii=False), msg_id),
        )
    return {
        "message_id": msg_id,
        "response_message_id": response_msg_id,
        "task_id": task_id,
        "context_id": context_id,
        "status": final_status,
        "result": invoke_result,
    }


def get_task(task_id: str) -> Optional[dict]:
    with _db() as conn:
        row = conn.execute("SELECT * FROM a2a_tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return None
        task = dict(row)
        task["history"] = json.loads(row["history_json"] or "[]")
        return task


def list_messages(task_id: str = "", to_agent: str = "", limit: int = 50) -> list[dict]:
    with _db() as conn:
        if task_id:
            rows = conn.execute(
                "SELECT * FROM a2a_messages WHERE task_id=? ORDER BY created_at LIMIT ?",
                (task_id, limit),
            ).fetchall()
        elif to_agent:
            rows = conn.execute(
                "SELECT * FROM a2a_messages WHERE to_agent=? ORDER BY created_at DESC LIMIT ?",
                (to_agent, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM a2a_messages ORDER BY created_at DESC LIMIT ?", (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def handle_request(payload: dict) -> dict:
    """A2A JSON-RPC 2.0 入口。"""
    req_id = payload.get("id")
    method = (payload.get("method") or "").strip()
    params = payload.get("params") or {}

    if method == "message/send":
        msg = params.get("message") or {}
        parts = msg.get("parts") or []
        text = next((p.get("text") for p in parts if p.get("kind") == "text"), "")
        return {"jsonrpc": "2.0", "id": req_id, "result": send_message(
            params.get("from", "tiangong"),
            msg.get("to") or params.get("to") or "guanwei",
            text,
            context_id=msg.get("contextId") or params.get("context_id") or "",
            task_id=msg.get("taskId"),
        )}

    if method == "tasks/get":
        return {"jsonrpc": "2.0", "id": req_id, "result": get_task(params.get("taskId") or "")}

    if method == "agents/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"agents": list_agents()}}

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"pong": True}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {
        "code": -32601, "message": f"Method not found: {method}"}}


def attach_flask_blueprint(url_prefix: str = "/a2a"):
    from flask import Blueprint, jsonify, request
    bp = Blueprint("aios_a2a", __name__, url_prefix=url_prefix)

    @bp.route("/", methods=["POST"])
    def rpc():
        payload = request.get_json(silent=True) or {}
        return jsonify(handle_request(payload))

    @bp.route("/agents", methods=["GET"])
    def agents():
        return jsonify({"agents": list_agents(), "count": len(list_agents())})

    @bp.route("/agents/<agent_id>", methods=["GET"])
    def agent(agent_id: str):
        return jsonify(get_agent(agent_id) or {"error": "not found"})

    @bp.route("/messages", methods=["GET", "POST"])
    def messages():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            return jsonify(send_message(
                data.get("from_agent", "tiangong"),
                data.get("to_agent", "guanwei"),
                data.get("text", ""),
                context_id=data.get("context_id", ""),
                task_id=data.get("task_id"),
            ))
        task_id = request.args.get("task_id", "")
        to_agent = request.args.get("to_agent", "")
        return jsonify({"messages": list_messages(task_id, to_agent)})

    @bp.route("/tasks/<task_id>", methods=["GET"])
    def task(task_id: str):
        return jsonify(get_task(task_id) or {"error": "not found"})

    return bp


def reset_for_tests(db_path: Optional[Path] = None) -> None:
    global A2A_DB_PATH
    target = db_path or A2A_DB_PATH
    if target.exists():
        target.unlink()
