"""MCP Gateway：JSON-RPC 2.0 协议骨架，包装 miniclaw.tools.global_tool_registry。

不部署真 MCP server，本地实现 MCP 协议核心方法：
- initialize: 返回 server 能力
- tools/list: 转换 BaseTool.to_schema 为 MCP Tool[]
- tools/call: 调用 global_tool_registry.call()，结构化 ToolResult 输出
- resources/list、prompts/list: 占位返回空

外部入口：
- handle_request(rpc_dict) -> rpc_response_dict：可被 Flask/FastAPI 直接暴露
- attach_flask_blueprint(bp): 在现有 Flask app 上挂 /mcp 端点
- attach_fastapi_router(app): 在 FastAPI 上挂 /mcp 路由
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger("aios_arch.mcp_gateway")

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "aios-mcp-gateway"
SERVER_VERSION = "0.1.0"


def _ensure_registry():
    """延迟导入 + 自动注册 system_tools，避免循环依赖。"""
    from miniclaw.tools import global_tool_registry
    if not global_tool_registry.list_tools():
        try:
            from miniclaw.builtins import system_tools
            from miniclaw.tools import BaseTool
            class _Api:
                def __init__(self):
                    self._registry = global_tool_registry
                def register_tool(self, tool):
                    self._registry.register(tool)
            system_tools.register(_Api())
        except Exception as exc:  # noqa: BLE001
            logger.warning("自动注册 system_tools 失败，仅返回已注册工具: %s", exc)
    return global_tool_registry


def _tool_to_mcp_schema(tool) -> dict:
    """把 BaseTool 转 MCP tools/list 的 Tool 结构。"""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for p in tool.parameters:
        prop: dict[str, Any] = {"type": p.type, "description": p.description}
        if getattr(p, "enum", None):
            prop["enum"] = p.enum
        if getattr(p, "default", None) is not None:
            prop["default"] = p.default
        properties[p.name] = prop
        if p.required:
            required.append(p.name)
    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def list_tools() -> list[dict]:
    registry = _ensure_registry()
    return [_tool_to_mcp_schema(t) for t in registry.get_all_tools()]


def call_tool(name: str, arguments: Optional[dict] = None) -> dict:
    registry = _ensure_registry()
    arguments = arguments or {}
    result = registry.call(name, **arguments)
    content: list[dict] = []
    if result.output:
        content.append({"type": "text", "text": result.output})
    if result.error:
        content.append({"type": "text", "text": f"[error] {result.error}"})
    return {
        "content": content,
        "isError": not result.success,
        "metadata": result.metadata,
        "tool": name,
    }


def _resp(result: Any, req_id: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(code: int, message: str, req_id: Any, data: Any = None) -> dict:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def handle_request(payload: dict) -> dict:
    """处理单条 JSON-RPC 2.0 请求，返回响应 dict。"""
    req_id = payload.get("id")
    method = (payload.get("method") or "").strip()
    params = payload.get("params") or {}

    if not payload.get("jsonrpc"):
        return _err(-32600, "Invalid Request: missing jsonrpc field", req_id)

    if method == "initialize":
        return _resp({
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": False},
                "prompts": {"listChanged": False},
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }, req_id)

    if method == "tools/list":
        return _resp({"tools": list_tools()}, req_id)

    if method == "tools/call":
        name = params.get("name") or ""
        if not name:
            return _err(-32602, "Invalid params: name required", req_id)
        try:
            return _resp(call_tool(name, params.get("arguments")), req_id)
        except Exception as exc:  # noqa: BLE001
            return _err(-32603, f"tool execution failed: {exc}", req_id)

    if method == "resources/list":
        return _resp({"resources": []}, req_id)

    if method == "prompts/list":
        return _resp({"prompts": []}, req_id)

    if method == "ping":
        return _resp({"pong": True, "server": SERVER_NAME}, req_id)

    return _err(-32601, f"Method not found: {method}", req_id)


def handle_batch(payload: Any) -> Any:
    """批量 JSON-RPC 请求。"""
    if isinstance(payload, list):
        return [handle_request(p) for p in payload if isinstance(p, dict)]
    return handle_request(payload if isinstance(payload, dict) else {})


def attach_flask_blueprint(url_prefix: str = "/mcp"):
    """把 MCP JSON-RPC 入口挂到 Flask 蓝图。"""
    from flask import Blueprint, Response, jsonify, request

    bp = Blueprint("aios_mcp", __name__, url_prefix=url_prefix)

    @bp.route("/", methods=["POST"])
    def rpc():
        payload = request.get_json(silent=True) or {}
        if isinstance(payload, list):
            return jsonify(handle_batch(payload))
        return jsonify(handle_request(payload))

    @bp.route("/tools", methods=["GET"])
    def tools():
        return jsonify({"tools": list_tools(), "count": len(list_tools())})

    @bp.route("/tools/<name>", methods=["POST"])
    def call(name: str):
        args = request.get_json(silent=True) or {}
        return jsonify(call_tool(name, args))

    @bp.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "server": SERVER_NAME, "version": SERVER_VERSION,
            "protocol": PROTOCOL_VERSION, "tools": len(list_tools()),
        })

    return bp


def attach_fastapi_router(app):
    """把 MCP 入口挂到 FastAPI 应用（可选）。"""
    if app is None:
        return None
    try:
        from fastapi import Request
        from fastapi.responses import JSONResponse
    except ModuleNotFoundError:
        return None

    @app.post("/mcp/")
    async def rpc(request: Request):
        payload = await request.json()
        if isinstance(payload, list):
            return JSONResponse(handle_batch(payload))
        return JSONResponse(handle_request(payload))

    @app.get("/mcp/tools")
    async def tools():
        return {"tools": list_tools(), "count": len(list_tools())}

    @app.post("/mcp/tools/{name}")
    async def call(name: str, request: Request):
        args = await request.json()
        return call_tool(name, args)

    return app
