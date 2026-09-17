"""MiniClaw 插件系统

模仿 OpenClaw 的 plugins/ 模块，提供插件发现、加载、注册和生命周期管理。
每个插件通过 register(api) 函数注册工具、钩子、HTTP路由等。
"""
import importlib
import logging
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field

from .hooks import HookRunner, HookContext, global_hook_runner
from .tools import BaseTool, ToolRegistry, global_tool_registry

logger = logging.getLogger("miniclaw.plugins")


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    enabled: bool = True


class PluginAPI:
    def __init__(self, manifest: PluginManifest, tool_registry: ToolRegistry, hook_runner: HookRunner):
        self.manifest = manifest
        self._tools = tool_registry
        self._hooks = hook_runner
        self._http_routes: List[Dict[str, Any]] = []
        self._commands: Dict[str, Callable] = {}
        self._services: List[Dict[str, Any]] = []

    def register_tool(self, tool: BaseTool) -> BaseTool:
        return self._tools.register(tool)

    def on(self, event: str, handler: Callable, priority: int = 100):
        self._hooks.on(event, handler, priority)

    def register_http_route(self, method: str, path: str, handler: Callable, description: str = ""):
        self._http_routes.append({
            "method": method.upper(),
            "path": path,
            "handler": handler,
            "description": description,
            "plugin": self.manifest.id,
        })

    def register_command(self, name: str, handler: Callable, description: str = ""):
        self._commands[name] = {
            "handler": handler,
            "description": description,
            "plugin": self.manifest.id,
        }

    def register_service(self, name: str, start_fn: Callable, stop_fn: Optional[Callable] = None):
        self._services.append({
            "name": name,
            "start": start_fn,
            "stop": stop_fn,
            "plugin": self.manifest.id,
        })


@dataclass
class PluginInstance:
    manifest: PluginManifest
    module: Any = None
    api: Optional[PluginAPI] = None
    loaded: bool = False
    error: Optional[str] = None


class PluginLoader:
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        hook_runner: Optional[HookRunner] = None,
    ):
        self._registry = tool_registry or global_tool_registry
        self._hooks = hook_runner or global_hook_runner
        self._plugins: Dict[str, PluginInstance] = {}

    def load_plugin(self, module_path: str, manifest: Optional[PluginManifest] = None) -> PluginInstance:
        plugin_id = manifest.id if manifest else module_path.split(".")[-1]
        if plugin_id in self._plugins and self._plugins[plugin_id].loaded:
            logger.warning(f"插件 '{plugin_id}' 已加载")
            return self._plugins[plugin_id]

        if not manifest:
            manifest = PluginManifest(
                id=plugin_id,
                name=plugin_id,
                description=f"插件 {module_path}",
            )

        instance = PluginInstance(manifest=manifest)
        try:
            module = importlib.import_module(module_path)
            instance.module = module
            api = PluginAPI(manifest, self._registry, self._hooks)
            instance.api = api

            if hasattr(module, "register") and callable(module.register):
                module.register(api)
            elif hasattr(module, "setup") and callable(module.setup):
                module.setup(api)

            instance.loaded = True
            self._plugins[plugin_id] = instance

            self._hooks.emit_sync("plugin_loaded", {
                "plugin_id": plugin_id,
                "manifest": manifest,
            })
            logger.info(f"插件加载成功: {manifest.name} v{manifest.version}")
        except Exception as e:
            instance.error = str(e)
            self._plugins[plugin_id] = instance
            logger.error(f"插件加载失败 [{plugin_id}]: {e}")

        return instance

    def unload_plugin(self, plugin_id: str) -> bool:
        instance = self._plugins.get(plugin_id)
        if not instance or not instance.loaded:
            return False
        try:
            if instance.api:
                for service in instance.api._services:
                    if service.get("stop"):
                        service["stop"]()
                for tool in self._registry.get_all_tools():
                    tool_type = type(tool)
                    if hasattr(instance.module, tool_type.__name__):
                        self._registry.unregister(tool.name)
            instance.loaded = False
            self._hooks.emit_sync("plugin_unloaded", {"plugin_id": plugin_id})
            logger.info(f"插件已卸载: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"插件卸载失败 [{plugin_id}]: {e}")
            return False

    def load_builtins(self, package: str = "miniclaw.builtins"):
        try:
            pkg = importlib.import_module(package)
            if hasattr(pkg, "__path__"):
                import pkgutil
                for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
                    full_path = f"{package}.{modname}"
                    self.load_plugin(full_path)
        except ImportError:
            logger.warning(f"内置插件包 '{package}' 不存在")

    def get_plugin(self, plugin_id: str) -> Optional[PluginInstance]:
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[Dict[str, Any]]:
        result = []
        for pid, inst in self._plugins.items():
            result.append({
                "id": pid,
                "name": inst.manifest.name,
                "version": inst.manifest.version,
                "loaded": inst.loaded,
                "error": inst.error,
            })
        return result

    def get_http_routes(self) -> List[Dict[str, Any]]:
        routes = []
        for inst in self._plugins.values():
            if inst.api:
                routes.extend(inst.api._http_routes)
        return routes

    def get_commands(self) -> Dict[str, Dict[str, Any]]:
        commands = {}
        for inst in self._plugins.values():
            if inst.api:
                commands.update(inst.api._commands)
        return commands


global_plugin_loader = PluginLoader()
