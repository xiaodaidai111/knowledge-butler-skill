"""MiniClaw 网关服务器

模仿 OpenClaw 的 gateway/ 模块，提供 HTTP API + WebSocket 实时通信。
网关是 MiniClaw 的核心运行时，负责接收请求、调用 Agent、返回结果。
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime

try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ModuleNotFoundError:  # Flask-only deployments do not need FastAPI.
    FastAPI = Request = WebSocket = WebSocketDisconnect = HTTPException = None
    CORSMiddleware = None

    class BaseModel:
        pass

from .config import MiniClawConfig
from .agent import MiniClawAgent
from .tools import global_tool_registry
from .hooks import global_hook_runner
from .plugins import PluginLoader, global_plugin_loader

logger = logging.getLogger("miniclaw.gateway")


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"
    stream: bool = False


class ConfigUpdateRequest(BaseModel):
    agent_model: Optional[str] = None
    agent_temperature: Optional[float] = None
    agent_max_tokens: Optional[int] = None
    agent_system_prompt: Optional[str] = None


class MiniClawGateway:
    def __init__(self, config: Optional[MiniClawConfig] = None):
        self.config = config or MiniClawConfig.load()
        self.agent = MiniClawAgent(config=self.config)
        self.plugin_loader = PluginLoader(
            tool_registry=global_tool_registry,
            hook_runner=global_hook_runner,
        )
        self.app: Optional[FastAPI] = None
        self._ws_connections: list = []
        self._started = False

    def setup(self):
        self.app = FastAPI(
            title="MiniClaw Gateway",
            description="微型插件驱动 AI 网关",
            version="0.1.0",
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._register_routes()
        self._register_plugin_routes()
        self._load_plugins()

    def _register_routes(self):
        app = self.app

        def _require_fastapi_auth(request: Request, roles: set[str] | None = None):
            from utils import decode_token

            roles = roles or {"admin", "operator"}
            token = request.headers.get("Authorization", "")
            if token.startswith("Bearer "):
                token = token[7:]
            payload = decode_token(token) if token else None
            if not payload:
                raise HTTPException(status_code=401, detail="missing or invalid token")
            role = str(payload.get("role") or payload.get("scope") or "operator")
            if role not in roles:
                raise HTTPException(status_code=403, detail="permission denied")
            return payload

        def _require_confirmed_fastapi_write(request: Request, payload: Dict[str, Any]):
            confirmed = payload.get("confirmed") is True or payload.get("confirm") is True
            idempotency_key = request.headers.get("Idempotency-Key") or str(payload.get("idempotency_key") or "").strip()
            if not confirmed:
                raise HTTPException(status_code=409, detail="write operation requires confirmed=true")
            if not idempotency_key:
                raise HTTPException(status_code=400, detail="write operation requires Idempotency-Key")

        @app.get("/miniclaw/health")
        async def health():
            return {
                "status": "healthy" if self._started else "starting",
                "version": "0.1.0",
                "tools_count": len(global_tool_registry),
                "plugins": self.plugin_loader.list_plugins(),
                "hooks": global_hook_runner.list_hooks(),
                "config": self.config.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }

        @app.post("/miniclaw/chat")
        async def chat(req: ChatRequest, request: Request):
            _require_fastapi_auth(request)
            if not req.message.strip():
                raise HTTPException(status_code=400, detail="消息不能为空")
            result = self.agent.process(req.message, req.conversation_id)
            return {
                "code": 200,
                "data": result.to_dict(),
            }

        @app.websocket("/miniclaw/ws")
        async def websocket_chat(websocket: WebSocket):
            await websocket.accept()
            self._ws_connections.append(websocket)
            try:
                while True:
                    data = await websocket.receive_json()
                    message = data.get("message", "")
                    conversation_id = data.get("conversation_id", "default")
                    if not message.strip():
                        await websocket.send_json({"error": "消息不能为空"})
                        continue
                    result = self.agent.process(message, conversation_id)
                    await websocket.send_json(result.to_dict())
            except WebSocketDisconnect:
                self._ws_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket 错误: {e}")
                if websocket in self._ws_connections:
                    self._ws_connections.remove(websocket)

        @app.get("/miniclaw/tools")
        async def list_tools():
            tools = []
            for tool in global_tool_registry.get_all_tools():
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": [
                        {"name": p.name, "type": p.type, "description": p.description, "required": p.required}
                        for p in tool.parameters
                    ],
                })
            return {"code": 200, "data": {"tools": tools, "count": len(tools)}}

        @app.get("/miniclaw/plugins")
        async def list_plugins():
            return {"code": 200, "data": self.plugin_loader.list_plugins()}

        @app.get("/miniclaw/hooks")
        async def list_hooks():
            return {"code": 200, "data": global_hook_runner.list_hooks()}

        @app.get("/miniclaw/config")
        async def get_config():
            return {"code": 200, "data": self.config.to_dict()}

        @app.put("/miniclaw/config")
        async def update_config(req: ConfigUpdateRequest, request: Request):
            _require_fastapi_auth(request, {"admin"})
            _require_confirmed_fastapi_write(request, req.model_dump(exclude_none=True))
            if req.agent_model:
                self.config.agent_model = req.agent_model
            if req.agent_temperature is not None:
                self.config.agent_temperature = req.agent_temperature
            if req.agent_max_tokens:
                self.config.agent_max_tokens = req.agent_max_tokens
            if req.agent_system_prompt:
                self.config.agent_system_prompt = req.agent_system_prompt
            self.agent = MiniClawAgent(config=self.config)
            return {"code": 200, "message": "配置已更新", "data": self.config.to_dict()}

        @app.post("/miniclaw/tools/{tool_name}/call")
        async def call_tool(tool_name: str, request: Request, args: Dict[str, Any] = None):
            args = args or {}
            _require_fastapi_auth(request)
            _require_confirmed_fastapi_write(request, args)
            result = global_tool_registry.call(tool_name, **args)
            return {
                "code": 200,
                "data": {
                    "tool": tool_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                },
            }

    def _register_plugin_routes(self):
        routes = self.plugin_loader.get_http_routes()
        for route in routes:
            method = route["method"]
            path = route["path"]
            handler = route["handler"]
            self.app.add_api_route(path, handler, methods=[method], name=f"plugin_{route['plugin']}_{path}")

    def _load_plugins(self):
        if self.config.plugins_enabled:
            self.plugin_loader.load_builtins("miniclaw.builtins")
            logger.info(f"已加载 {len(self.plugin_loader.list_plugins())} 个插件")

    def start(self, host: Optional[str] = None, port: Optional[int] = None):
        host = host or self.config.gateway_host
        port = port or self.config.gateway_port

        if not self.app:
            self.setup()

        self._started = True
        global_hook_runner.emit_sync("gateway_start", {
            "host": host,
            "port": port,
        })

        logger.info(f"MiniClaw 网关启动: http://{host}:{port}")
        logger.info(f"  工具数: {len(global_tool_registry)}")
        logger.info(f"  插件数: {len(self.plugin_loader.list_plugins())}")

        import uvicorn
        uvicorn.run(self.app, host=host, port=port, log_level="info")

    def stop(self):
        self._started = False
        global_hook_runner.emit_sync("gateway_stop", {})
        logger.info("MiniClaw 网关已停止")

    def create_flask_blueprint(self):
        from flask import Blueprint, request, jsonify, Response
        import json as flask_json
        from security import require_confirmed_write

        bp = Blueprint("miniclaw", __name__)

        @bp.route("/miniclaw/health", methods=["GET"])
        def health():
            return jsonify({
                "status": "healthy",
                "version": "0.1.0",
                "tools_count": len(global_tool_registry),
                "plugins": self.plugin_loader.list_plugins(),
                "timestamp": datetime.now().isoformat(),
            })

        @bp.route("/miniclaw/chat", methods=["POST"])
        def chat():
            data = request.get_json(silent=True) or {}
            message = data.get("message", "").strip()
            conversation_id = data.get("conversation_id", "default")
            if not message:
                return jsonify({"code": 400, "message": "消息不能为空"}), 400
            result = self.agent.process(message, conversation_id)
            return jsonify({"code": 200, "data": result.to_dict()})

        @bp.route("/miniclaw/stream", methods=["POST"])
        def stream_chat():
            data = request.get_json(silent=True) or {}
            message = data.get("message", "").strip()
            conversation_id = data.get("conversation_id", "default")
            if not message:
                return jsonify({"code": 400, "message": "消息不能为空"}), 400

            def generate():
                result = self.agent.process(message, conversation_id)
                yield flask_json.dumps({"type": "result", "data": result.to_dict()}, ensure_ascii=False) + "\n"

            return Response(generate(), mimetype="text/event-stream")

        @bp.route("/miniclaw/tools", methods=["GET"])
        def list_tools():
            tools = []
            for tool in global_tool_registry.get_all_tools():
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": [
                        {"name": p.name, "type": p.type, "description": p.description, "required": p.required}
                        for p in tool.parameters
                    ],
                })
            return jsonify({"code": 200, "data": {"tools": tools, "count": len(tools)}})

        @bp.route("/miniclaw/plugins", methods=["GET"])
        def list_plugins():
            return jsonify({"code": 200, "data": self.plugin_loader.list_plugins()})

        @bp.route("/miniclaw/hooks", methods=["GET"])
        def list_hooks():
            return jsonify({"code": 200, "data": global_hook_runner.list_hooks()})

        @bp.route("/miniclaw/config", methods=["GET"])
        def get_config():
            return jsonify({"code": 200, "data": self.config.to_dict()})

        @bp.route("/miniclaw/tools/<tool_name>/call", methods=["POST"])
        @require_confirmed_write("miniclaw.tool_call", "/miniclaw/tools/<tool_name>/call")
        def call_tool(tool_name):
            args = request.get_json(silent=True) or {}
            result = global_tool_registry.call(tool_name, **args)
            return jsonify({
                "code": 200,
                "data": {
                    "tool": tool_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                },
            })

        return bp
