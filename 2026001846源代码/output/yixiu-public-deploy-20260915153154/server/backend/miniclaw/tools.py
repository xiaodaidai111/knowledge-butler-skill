"""MiniClaw 工具系统

模仿 OpenClaw 的 agents/tools/ 模块，提供工具基类、注册表和调用器。
每个工具通过插件系统注册，Agent 通过工具注册表发现和调用工具。
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field

logger = logging.getLogger("miniclaw.tools")


@dataclass
class ToolParameter:
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters: List[ToolParameter] = field(default_factory=list)

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        pass

    def to_schema(self) -> Dict[str, Any]:
        properties = {}
        required = []
        for param in self.parameters:
            prop: Dict[str, Any] = {"type": param.type, "description": param.description}
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop
            if param.required:
                required.append(param.name)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_description(self) -> str:
        param_desc = ""
        for p in self.parameters:
            req = "必填" if p.required else "可选"
            default = f", 默认={p.default}" if p.default is not None else ""
            param_desc += f"  - {p.name} ({p.type}, {req}{default}): {p.description}\n"
        return f"工具: {self.name}\n描述: {self.description}\n参数:\n{param_desc}"


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}

    def register(self, tool: BaseTool) -> BaseTool:
        if tool.name in self._tools:
            logger.warning(f"工具 '{tool.name}' 已存在，将被覆盖")
        self._tools[tool.name] = tool
        self._tool_classes[tool.name] = type(tool)
        logger.info(f"工具注册: {tool.name}")
        return tool

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            self._tool_classes.pop(name, None)
            logger.info(f"工具注销: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_all_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tools_description(self) -> str:
        if not self._tools:
            return "当前没有可用工具。"
        descriptions = []
        for tool in self._tools.values():
            descriptions.append(tool.to_description())
        return "\n".join(descriptions)

    def call(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, output="", error=f"工具 '{name}' 不存在")
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"工具调用错误 [{name}]: {e}")
            return ToolResult(success=False, output="", error=f"工具执行错误: {str(e)}")

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


global_tool_registry = ToolRegistry()
