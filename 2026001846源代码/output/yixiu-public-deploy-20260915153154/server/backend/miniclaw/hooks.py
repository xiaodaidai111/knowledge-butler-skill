"""MiniClaw 钩子系统

模仿 OpenClaw 的 hooks/ 模块，提供生命周期钩子注册与触发。
支持的钩子事件：
  - before_agent_start / after_agent_start
  - before_tool_call / after_tool_call
  - before_llm_call / after_llm_call
  - message_received / message_sent
  - plugin_loaded / plugin_unloaded
  - gateway_start / gateway_stop
"""
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("miniclaw.hooks")


@dataclass
class HookContext:
    event: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False
    modified_data: Optional[Dict[str, Any]] = None

    def cancel(self):
        self.cancelled = True

    def modify(self, key: str, value: Any):
        if self.modified_data is None:
            self.modified_data = {}
        self.modified_data[key] = value


HookHandler = Callable[[HookContext], Optional[HookContext]]


class HookRunner:
    def __init__(self):
        self._hooks: Dict[str, List[HookHandler]] = {}
        self._hooks_by_priority: Dict[str, List[tuple]] = {}

    def on(self, event: str, handler: HookHandler, priority: int = 100):
        if event not in self._hooks_by_priority:
            self._hooks_by_priority[event] = []
        self._hooks_by_priority[event].append((priority, handler))
        self._hooks_by_priority[event].sort(key=lambda x: x[0])
        self._hooks[event] = [h for _, h in self._hooks_by_priority[event]]
        logger.debug(f"钩子注册: {event} (priority={priority})")

    def off(self, event: str, handler: Optional[HookHandler] = None):
        if handler:
            if event in self._hooks:
                self._hooks[event] = [h for h in self._hooks[event] if h != handler]
            if event in self._hooks_by_priority:
                self._hooks_by_priority[event] = [
                    (p, h) for p, h in self._hooks_by_priority[event] if h != handler
                ]
        else:
            self._hooks.pop(event, None)
            self._hooks_by_priority.pop(event, None)

    async def emit(self, event: str, data: Optional[Dict[str, Any]] = None) -> HookContext:
        ctx = HookContext(event=event, data=data or {})
        handlers = self._hooks.get(event, [])
        for handler in handlers:
            try:
                result = handler(ctx)
                if result is not None:
                    ctx = result
                if ctx.cancelled:
                    logger.debug(f"钩子 {event} 被取消")
                    break
                if ctx.modified_data:
                    ctx.data.update(ctx.modified_data)
                    ctx.modified_data = None
            except Exception as e:
                logger.error(f"钩子处理器错误 [{event}]: {e}")
        return ctx

    def emit_sync(self, event: str, data: Optional[Dict[str, Any]] = None) -> HookContext:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self.emit(event, data))
                return future.result()
        return asyncio.run(self.emit(event, data))

    def list_hooks(self) -> Dict[str, int]:
        return {event: len(handlers) for event, handlers in self._hooks.items()}


_builtin_events = [
    "before_agent_start",
    "after_agent_start",
    "before_tool_call",
    "after_tool_call",
    "before_llm_call",
    "after_llm_call",
    "message_received",
    "message_sent",
    "plugin_loaded",
    "plugin_unloaded",
    "gateway_start",
    "gateway_stop",
]

global_hook_runner = HookRunner()
