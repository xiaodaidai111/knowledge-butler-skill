"""API Gateway 中间件：JWT auth + rate-limit，包装 Flask 蓝图。

提供 Flask 装饰器 `require_gateway_auth` 和 `rate_limit`，以及
`mount_gateway_blueprints(app)` 一次性挂载 aios_arch 全套蓝图：
- /mcp/*        MCP Gateway
- /a2a/*        A2A Registry
- /sandbox/*    Sandbox Pool
- /trace/*      Trace 落盘
- /opa/*        OPA 策略
- /memory/*     Memory Layer
- /api/aios-arch/supervisor/*  LangGraph Supervisor

所有 write 类入口走 require_gateway_auth + rate_limit + OPA 二次求值。
"""
from __future__ import annotations

import functools
import logging
import time
from collections import defaultdict
from typing import Callable, Optional

from flask import Blueprint, g, jsonify, request

logger = logging.getLogger("aios_arch.api_gateway")

# 简单内存限流：{(user_id, window_start): count}
_RATE_BUCKETS: dict[tuple[str, float], int] = defaultdict(int)
_DEFAULT_WINDOW = 60.0
_DEFAULT_MAX_CALLS = 60


def require_gateway_auth(roles: Optional[set[str]] = None) -> Callable:
    """JWT 鉴权装饰器，复用 utils.decode_token。"""
    allowed = roles or {"admin", "operator", "auditor"}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from utils import decode_token
            token_value = request.headers.get("Authorization", "")
            if token_value.startswith("Bearer "):
                token_value = token_value[7:]
            payload = decode_token(token_value) if token_value else None
            if not payload:
                return jsonify({"code": 401, "message": "missing or invalid token"}), 401
            role = str(payload.get("role") or payload.get("scope") or "operator")
            g.actor = {"user_id": payload.get("user_id"), "role": role, "claims": payload}
            if role not in allowed:
                return jsonify({"code": 403, "message": "permission denied"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(window_seconds: float = _DEFAULT_WINDOW,
               max_calls: int = _DEFAULT_MAX_CALLS) -> Callable:
    """内存限流装饰器：按 user_id + 时间窗。"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            actor = getattr(g, "actor", None) or {}
            user_id = str(actor.get("user_id") or "anonymous")
            now = time.time()
            window_start = int(now // window_seconds) * window_seconds
            key = (user_id, window_start)
            current = _RATE_BUCKETS[key]
            if current >= max_calls:
                return jsonify({
                    "code": 429,
                    "message": f"rate limit exceeded: {max_calls}/{int(window_seconds)}s",
                }), 429
            _RATE_BUCKETS[key] = current + 1
            return func(*args, **kwargs)
        return wrapper
    return decorator


def _build_sandbox_blueprint() -> Blueprint:
    bp = Blueprint("aios_sandbox", __name__, url_prefix="/sandbox")
    from aios_arch.sandbox_pool import run_code, list_runs, get_run

    @bp.route("/run", methods=["POST"])
    @require_gateway_auth({"admin"})
    @rate_limit(window_seconds=60, max_calls=20)
    def run():
        payload = request.get_json(silent=True) or {}
        code = str(payload.get("code") or "")
        if not code:
            return jsonify({"code": 400, "message": "code 不能为空"}), 400
        return jsonify(run_code(
            code=code,
            language=payload.get("language", "python"),
            timeout=int(payload.get("timeout", 10)),
            memory_limit_mb=payload.get("memory_limit_mb"),
            stdin=payload.get("stdin", ""),
        ))

    @bp.route("/runs", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def runs():
        return jsonify({"runs": list_runs(limit=int(request.args.get("limit", 50)))})

    @bp.route("/runs/<run_id>", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def run_detail(run_id: str):
        return jsonify(get_run(run_id) or {"error": "not found"})

    return bp


def _build_trace_blueprint() -> Blueprint:
    bp = Blueprint("aios_trace", __name__, url_prefix="/trace")
    from aios_arch.trace import list_traces, get_trace, export_batch

    @bp.route("/traces", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def traces():
        return jsonify({"traces": list_traces(
            limit=int(request.args.get("limit", 50)),
            name_like=request.args.get("name", ""),
        )})

    @bp.route("/traces/<trace_id>", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def trace_detail(trace_id: str):
        return jsonify(get_trace(trace_id) or {"error": "not found"})

    @bp.route("/export", methods=["GET"])
    @require_gateway_auth({"admin"})
    def export():
        return jsonify(export_batch(limit=int(request.args.get("limit", 100))))

    return bp


def _build_opa_blueprint() -> Blueprint:
    bp = Blueprint("aios_opa", __name__, url_prefix="/opa")
    from aios_arch.opa_guard import list_policies, list_decisions, evaluate

    @bp.route("/policies", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def policies():
        return jsonify({"policies": list_policies(only_enabled=bool(
            request.args.get("enabled", "false").lower() == "true"))})

    @bp.route("/decisions", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def decisions():
        return jsonify({"decisions": list_decisions(
            trace_id=request.args.get("trace_id", ""),
            limit=int(request.args.get("limit", 100)),
        )})

    @bp.route("/evaluate", methods=["POST"])
    @require_gateway_auth({"admin"})
    def eval_endpoint():
        payload = request.get_json(silent=True) or {}
        return jsonify(evaluate(
            action=payload.get("action", ""),
            resource=payload.get("resource", ""),
            payload=payload.get("payload", {}),
            actor=payload.get("actor") or getattr(g, "actor", {"user_id": "anonymous", "role": "operator"}),
            context=payload.get("context", {}),
            trace_id=payload.get("trace_id", ""),
        ))

    return bp


def _build_memory_blueprint() -> Blueprint:
    bp = Blueprint("aios_memory", __name__, url_prefix="/memory")
    from aios_arch.memory_layer import add, search, get, list_memories, update, delete

    @bp.route("/memories", methods=["POST"])
    @require_gateway_auth({"admin", "operator"})
    def add_memory():
        payload = request.get_json(silent=True) or {}
        mem_id = add(
            user_id=payload.get("user_id", ""),
            agent_id=payload.get("agent_id", ""),
            content=payload.get("content", ""),
            metadata=payload.get("metadata"),
        )
        return jsonify({"memory_id": mem_id})

    @bp.route("/memories/search", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def search_memory():
        return jsonify({"hits": search(
            user_id=request.args.get("user_id", ""),
            query=request.args.get("q", ""),
            agent_id=request.args.get("agent_id", ""),
            top_k=int(request.args.get("top_k", 5)),
        )})

    @bp.route("/memories", methods=["GET"])
    @require_gateway_auth({"admin", "operator", "auditor"})
    def list_memory():
        return jsonify({"memories": list_memories(
            user_id=request.args.get("user_id", ""),
            agent_id=request.args.get("agent_id", ""),
            limit=int(request.args.get("limit", 50)),
        )})

    @bp.route("/memories/<mem_id>", methods=["GET", "PUT", "DELETE"])
    @require_gateway_auth({"admin", "operator"})
    def memory_detail(mem_id: str):
        if request.method == "GET":
            return jsonify(get(mem_id) or {"error": "not found"})
        if request.method == "DELETE":
            ok = delete(mem_id)
            return jsonify({"deleted": ok})
        payload = request.get_json(silent=True) or {}
        ok = update(mem_id, content=payload.get("content", ""),
                    metadata=payload.get("metadata"))
        return jsonify({"updated": ok, "memory": get(mem_id)})

    return bp


def _build_supervisor_blueprint() -> Blueprint:
    bp = Blueprint("aios_supervisor", __name__, url_prefix="/api/aios-arch/supervisor")
    from aios_runtime import supervisor_execute

    @bp.route("/run", methods=["POST"])
    @require_gateway_auth({"admin", "operator"})
    @rate_limit(window_seconds=60, max_calls=10)
    def run_supervisor():
        payload = request.get_json(silent=True) or {}
        goal = str(payload.get("goal") or "").strip()
        if not goal:
            return jsonify({"code": 400, "message": "goal 不能为空"}), 400
        outcome = supervisor_execute(
            goal=goal,
            mode=payload.get("mode", "auto"),
            task_id=payload.get("task_id", ""),
            execute_all=bool(payload.get("execute_all", True)),
            approve_all=bool(payload.get("approve_all", True)),
            actor=getattr(g, "actor", None) or None,
            session_id=payload.get("session_id", ""),
        )
        return jsonify({"code": 200, "data": outcome})

    return bp


def mount_gateway_blueprints(app) -> None:
    """把 aios_arch 全套蓝图挂到 Flask app。"""
    try:
        from aios_arch.mcp_gateway import attach_flask_blueprint as attach_mcp
        app.register_blueprint(attach_mcp(url_prefix="/mcp"))
        logger.info("/mcp mounted")
    except Exception as exc:  # noqa: BLE001
        logger.error("mcp mount failed: %s", exc)

    try:
        from aios_arch.a2a_registry import attach_flask_blueprint as attach_a2a
        app.register_blueprint(attach_a2a(url_prefix="/a2a"))
        logger.info("/a2a mounted")
    except Exception as exc:  # noqa: BLE001
        logger.error("a2a mount failed: %s", exc)

    for builder in (_build_sandbox_blueprint, _build_trace_blueprint,
                    _build_opa_blueprint, _build_memory_blueprint,
                    _build_supervisor_blueprint):
        try:
            app.register_blueprint(builder())
            logger.info("%s mounted", builder.__name__)
        except Exception as exc:  # noqa: BLE001
            logger.error("%s mount failed: %s", builder.__name__, exc)
