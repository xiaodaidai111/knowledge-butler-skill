"""一修 MCP Server —— 把大模型对话上下文上传到一修 Team Memory 系统。

用法:
  python mcp_yixiu_server.py          # stdio 模式（默认）
  python mcp_yixiu_server.py --sse    # SSE 模式（端口 3000）

环境变量:
  YIXIU_API_BASE  后端地址，默认 http://localhost:5000
  YIXIU_JWT_TOKEN JWT Token（可选，不填则匿名访问）
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from typing import Any, Optional

import httpx

# ─── 配置 ───────────────────────────────────────────────────────────────────

API_BASE = os.getenv("YIXIU_API_BASE", "http://localhost:5000")
JWT_TOKEN = os.getenv("YIXIU_JWT_TOKEN", "")
YIXIU_ACCOUNT = os.getenv("YIXIU_ACCOUNT", "mcp-user")

logger = logging.getLogger("mcp_yixiu")

# ─── Token 管理 ──────────────────────────────────────────────────────────────

_token_cache: dict[str, str] = {"token": "", "account": ""}


def _ensure_token() -> str:
    """确保有可用的 JWT Token，没有则自动登录获取。"""
    if JWT_TOKEN:
        return JWT_TOKEN
    if _token_cache["token"] and _token_cache["account"] == YIXIU_ACCOUNT:
        return _token_cache["token"]
    # 自动登录
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{API_BASE}/api/yixiu/session",
                json={"account": YIXIU_ACCOUNT, "name": YIXIU_ACCOUNT},
                headers={"Content-Type": "application/json"},
            )
            data = resp.json()
            token = data.get("data", {}).get("token", "")
            if token:
                _token_cache["token"] = token
                _token_cache["account"] = YIXIU_ACCOUNT
                logger.info("自动登录成功，account=%s", YIXIU_ACCOUNT)
                return token
    except Exception as e:
        logger.warning("自动登录失败: %s", e)
    return ""

# ─── MCP 协议常量 ────────────────────────────────────────────────────────────

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "yixiu-context-uploader"
SERVER_VERSION = "1.0.0"

# ─── 工具定义 ────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "upload_context",
        "description": "把大模型对话上下文（完整聊天记录）上传到一修 Team Memory 系统，生成一条 Memory Unit。适用于沉淀有价值的对话过程、技术讨论、问题排查等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "记忆标题，简洁概括对话主题，如：支付回调幂等处理讨论"
                },
                "messages": {
                    "type": "array",
                    "description": "对话消息列表，每条包含 role 和 content",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["user", "assistant", "system"], "description": "消息角色"},
                            "content": {"type": "string", "description": "消息内容"}
                        },
                        "required": ["role", "content"]
                    }
                },
                "project": {
                    "type": "string",
                    "description": "所属项目名称，如：支付服务、权限模块"
                },
                "tech_stack": {
                    "type": "string",
                    "description": "技术栈，如：Node.js + MySQL、Vue + Flask"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "自定义标签，如：['支付', '幂等', 'Bug修复']"
                },
                "source": {
                    "type": "string",
                    "description": "来源标识，如：Claude Code、Cursor、opencode"
                }
            },
            "required": ["title", "messages"]
        }
    },
    {
        "name": "upload_memory",
        "description": "上传一条结构化的 Memory Unit 到一修系统。适用于已有明确的问题、根因、方案的场景。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "记忆标题"
                },
                "problem": {
                    "type": "string",
                    "description": "遇到的问题描述"
                },
                "solution": {
                    "type": "string",
                    "description": "最终解决方案"
                },
                "root_cause": {
                    "type": "string",
                    "description": "根本原因分析"
                },
                "project": {
                    "type": "string",
                    "description": "所属项目"
                },
                "tech_stack": {
                    "type": "string",
                    "description": "技术栈"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签"
                },
                "applicable_when": {
                    "type": "string",
                    "description": "适用场景说明"
                },
                "source": {
                    "type": "string",
                    "description": "来源标识"
                }
            },
            "required": ["title", "problem", "solution"]
        }
    },
    {
        "name": "list_memories",
        "description": "列出一修系统中的 Team Memory 条目。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（可选）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回条数，默认 10",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_system_overview",
        "description": "获取一修系统概览：在线设备、待处理告警、今日任务等。",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

# ─── 后端 API 调用 ────────────────────────────────────────────────────────────

def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    token = _ensure_token()
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _api_post(path: str, data: dict) -> dict:
    url = f"{API_BASE}{path}"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=data, headers=_headers())
            return resp.json()
    except Exception as e:
        return {"code": 500, "message": f"请求失败: {e}"}


def _api_get(path: str) -> dict:
    url = f"{API_BASE}{path}"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=_headers())
            return resp.json()
    except Exception as e:
        return {"code": 500, "message": f"请求失败: {e}"}


# ─── 工具实现 ────────────────────────────────────────────────────────────────

def _format_conversation(messages: list[dict]) -> str:
    """把消息列表格式化为可读的对话记录。"""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        role_label = {"user": "用户", "assistant": "AI", "system": "系统"}.get(role, role)
        lines.append(f"【{role_label}】{content}")
    return "\n\n".join(lines)


def _build_memory_content(title: str, messages: list[dict], project: str = "",
                          tech_stack: str = "", extra: str = "") -> str:
    """根据对话构建 Memory Unit 的 content 字段。"""
    conversation = _format_conversation(messages)
    sections = [f"# {title}\n"]

    if project or tech_stack:
        sections.append("## 适用范围")
        if project:
            sections.append(f"- 项目：{project}")
        if tech_stack:
            sections.append(f"- 技术栈：{tech_stack}")
        sections.append("")

    sections.append("## 对话上下文\n")
    sections.append(conversation)
    sections.append("")

    if extra:
        sections.append(f"## 补充说明\n{extra}\n")

    sections.append("## 验证与审核\n此 Memory 由 MCP 上下文上传工具自动生成，待人工审核后入库。")
    return "\n".join(sections)


def tool_upload_context(args: dict) -> dict:
    title = args.get("title", "").strip()
    messages = args.get("messages", [])
    project = args.get("project", "")
    tech_stack = args.get("tech_stack", "")
    tags = args.get("tags", ["MCP上传", "对话上下文"])
    source = args.get("source", "MCP Server")

    if not title:
        return {"content": [{"type": "text", "text": "错误：title 不能为空"}], "isError": True}
    if not messages:
        return {"content": [{"type": "text", "text": "错误：messages 不能为空"}], "isError": True}

    # 确保 tags 包含来源标识
    if "MCP上传" not in tags:
        tags.insert(0, "MCP上传")

    content = _build_memory_content(title, messages, project, tech_stack)

    payload = {
        "title": title,
        "summary": f"[MCP上传] {title} — 共 {len(messages)} 条消息",
        "content": content,
        "type": "Memory Unit",
        "category": "团队记忆",
        "equipment": project or "通用项目",
        "model": tech_stack or "通用技术栈",
        "tags": tags,
        "source": source,
        "confirmed": True,
        "idempotency_key": f"mcp-{int(time.time())}-{hash(title) % 10000}"
    }

    result = _api_post("/api/yixiu/knowledge/update", payload)

    if result.get("code") == 200 or result.get("data"):
        item = result.get("data", {})
        return {
            "content": [{
                "type": "text",
                "text": f"✅ 对话上下文已上传到一修系统\n\n"
                        f"**ID**: {item.get('id', 'N/A')}\n"
                        f"**标题**: {title}\n"
                        f"**消息数**: {len(messages)} 条\n"
                        f"**状态**: {item.get('status', 'pending')}（待人工审核）\n"
                        f"**标签**: {', '.join(tags)}\n\n"
                        f"请在「Memory Evolution」页面审核入库。"
            }]
        }
    else:
        return {
            "content": [{"type": "text", "text": f"上传失败：{result.get('message', '未知错误')}"}],
            "isError": True
        }


def tool_upload_memory(args: dict) -> dict:
    title = args.get("title", "").strip()
    problem = args.get("problem", "").strip()
    solution = args.get("solution", "").strip()
    root_cause = args.get("root_cause", "")
    project = args.get("project", "")
    tech_stack = args.get("tech_stack", "")
    tags = args.get("tags", ["MCP上传", "结构化Memory"])
    applicable_when = args.get("applicable_when", "")
    source = args.get("source", "MCP Server")

    if not title:
        return {"content": [{"type": "text", "text": "错误：title 不能为空"}], "isError": True}
    if not problem:
        return {"content": [{"type": "text", "text": "错误：problem 不能为空"}], "isError": True}
    if not solution:
        return {"content": [{"type": "text", "text": "错误：solution 不能为空"}], "isError": True}

    # 构建结构化内容
    sections = [f"# {title}\n"]
    if project or tech_stack:
        sections.append("## 适用范围")
        if project:
            sections.append(f"- 项目：{project}")
        if tech_stack:
            sections.append(f"- 技术栈：{tech_stack}")
        sections.append("")

    sections.append(f"## 问题\n{problem}\n")
    if root_cause:
        sections.append(f"## 根因分析\n{root_cause}\n")
    sections.append(f"## 解决方案\n{solution}\n")
    if applicable_when:
        sections.append(f"## 适用场景\n{applicable_when}\n")
    sections.append("## 验证与审核\n此 Memory 由 MCP 结构化上传工具自动生成，待人工审核后入库。")

    content = "\n".join(sections)
    summary = f"[MCP上传] {title}：{problem[:80]}..."

    payload = {
        "title": title,
        "summary": summary,
        "content": content,
        "type": "Memory Unit",
        "category": "团队记忆",
        "equipment": project or "通用项目",
        "model": tech_stack or "通用技术栈",
        "tags": tags,
        "source": source,
        "confirmed": True,
        "idempotency_key": f"mcp-mem-{int(time.time())}-{hash(title) % 10000}"
    }

    result = _api_post("/api/yixiu/knowledge/update", payload)

    if result.get("code") == 200 or result.get("data"):
        item = result.get("data", {})
        return {
            "content": [{
                "type": "text",
                "text": f"✅ 结构化 Memory 已上传\n\n"
                        f"**ID**: {item.get('id', 'N/A')}\n"
                        f"**标题**: {title}\n"
                        f"**状态**: {item.get('status', 'pending')}（待审核）\n\n"
                        f"请在「Memory Evolution」页面审核入库。"
            }]
        }
    else:
        return {
            "content": [{"type": "text", "text": f"上传失败：{result.get('message', '未知错误')}"}],
            "isError": True
        }


def tool_list_memories(args: dict) -> dict:
    keyword = args.get("keyword", "")
    limit = args.get("limit", 10)

    path = f"/api/yixiu/knowledge?limit={limit}"
    if keyword:
        path += f"&keyword={keyword}"

    result = _api_get(path)

    if result.get("code") == 200 or result.get("data"):
        items = result.get("data", {})
        if isinstance(items, dict):
            items = items.get("items", [])
        if not items:
            return {"content": [{"type": "text", "text": "暂无 Memory 条目"}]}

        lines = [f"📋 一修 Team Memory（共 {len(items)} 条）\n"]
        for item in items[:limit]:
            status_icon = {"approved": "✅", "pending": "⏳", "rejected": "❌"}.get(item.get("status", ""), "❓")
            lines.append(f"{status_icon} **{item.get('title', 'N/A')}**")
            lines.append(f"   ID: {item.get('id', 'N/A')} | 状态: {item.get('status', 'N/A')}")
            lines.append(f"   摘要: {(item.get('summary', '') or '')[:100]}")
            lines.append("")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}
    else:
        return {
            "content": [{"type": "text", "text": f"查询失败：{result.get('message', '未知错误')}"}],
            "isError": True
        }


def tool_get_system_overview(args: dict) -> dict:
    result = _api_get("/api/dashboard/overview")

    if result.get("code") == 200:
        stats = result.get("data", {})
        text = (
            f"📊 一修系统概览\n\n"
            f"- 在线设备：{stats.get('online_equipment', 0)}\n"
            f"- 待处理告警：{stats.get('pending_alerts', 0)}\n"
            f"- 待审核案例：{stats.get('pending_reviews', 0)}\n"
            f"- 今日检修任务：{stats.get('today_tasks', 0)}\n"
        )
        return {"content": [{"type": "text", "text": text}]}
    else:
        return {
            "content": [{"type": "text", "text": f"获取系统概览失败：{result.get('message', '未知错误')}"}],
            "isError": True
        }


# ─── 工具路由 ────────────────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "upload_context": tool_upload_context,
    "upload_memory": tool_upload_memory,
    "list_memories": tool_list_memories,
    "get_system_overview": tool_get_system_overview,
}

# ─── JSON-RPC 2.0 处理 ──────────────────────────────────────────────────────

def handle_rpc(payload: dict) -> dict:
    req_id = payload.get("id")
    method = (payload.get("method") or "").strip()
    params = payload.get("params") or {}

    def ok(result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def err(code, message):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    if method == "initialize":
        return ok({
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method == "notifications/initialized":
        return ok({})

    if method == "ping":
        return ok({"pong": True})

    if method == "tools/list":
        return ok({"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return err(-32602, f"Unknown tool: {name}")
        try:
            return ok(handler(arguments))
        except Exception as e:
            return err(-32603, f"Tool execution failed: {e}")

    if method in ("resources/list", "prompts/list"):
        return ok({"resources": [], "prompts": []})

    return err(-32601, f"Method not found: {method}")


# ─── Stdio 传输 ──────────────────────────────────────────────────────────────

def run_stdio():
    """通过 stdin/stdout 运行 MCP Server（标准模式）。"""
    logger.info("一修 MCP Server 启动（stdio 模式）")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_rpc(payload)
        if response:
            print(json.dumps(response), flush=True)


# ─── SSE 传输 ────────────────────────────────────────────────────────────────

def run_sse(port: int = 3000):
    """通过 HTTP SSE 运行 MCP Server。"""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class MCPHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                return
            response = handle_rpc(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "server": SERVER_NAME}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            logger.info(format % args)

    server = HTTPServer(("0.0.0.0", port), MCPHandler)
    logger.info(f"一修 MCP Server 启动（SSE 模式，端口 {port}）")
    logger.info(f"健康检查: http://localhost:{port}/health")
    server.serve_forever()


# ─── 入口 ────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="一修 MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE 模式")
    parser.add_argument("--port", type=int, default=3000, help="SSE 模式端口")
    args = parser.parse_args()

    if args.sse:
        run_sse(args.port)
    else:
        run_stdio()


if __name__ == "__main__":
    main()
