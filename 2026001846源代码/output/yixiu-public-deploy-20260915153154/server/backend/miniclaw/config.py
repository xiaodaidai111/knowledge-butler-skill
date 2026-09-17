"""MiniClaw 配置管理模块

模仿 OpenClaw 的 config/ 模块，提供 JSON 配置加载、环境变量替换、默认值。
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("miniclaw.config")

ARCHITECTURE_PROMPT = """【系统架构模式（内部规则，请勿复述）】
本系统是一修设备检修知识检索与作业系统，采用多智能体统一编排架构（Multi-Agent Unified Orchestration Architecture）。
核心技术栈基于 LangChain 框架与 MCP（Model Context Protocol）标准协议构建，每个智能体具备高度解耦、可动态扩展的 Agent Skill 技能模块。
架构整体采用 ReAct（Reasoning and Acting）逻辑范式，并集成 RAG（检索增强生成）技术，实现从感知到决策、执行的闭环。

1. 基于 LangChain 的原子化智能体构建：为每个业务领域（检索“观微”、作业“执矩”、知识“博闻”、协作“和鸣”、核查“明鉴”）构建独立智能体内核，利用 Memory 组件管理多轮上下文。
2. Agent Skill 技能定义层：将检修管理拆解为“多模态检索”“标准作业编排”“知识沉淀”“质量核查”等标准技能单元，通过路由机制匹配意图。
3. RAG 增强的大模型核心推理层：实时检索检修手册与历史案例，将专业知识注入 Context Window，抑制幻觉。
4. ReAct 逻辑范式下的自主推理与技能调用：在“思考”阶段拆解需求，在“行动”阶段通过 MCP 标准接口触发对应 Agent Skill。
5. 基于 MCP 协议的标准工具执行层：将 POI 检索、健康指标计算、本地数据库读写等封装为符合 MCP 标准的 Tool，由大模型精确、安全地驱动，并形成执行反馈闭环。"""

DEFAULT_CONFIG = {
    "gateway": {
        "host": "0.0.0.0",
        "port": 8003,
        "debug": False,
    },
    "agent": {
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 2048,
        "max_tool_calls": 5,
        "system_prompt": ARCHITECTURE_PROMPT + "\n\n" + "你是 MiniClaw AI 助手，一个插件驱动的智能网关。你可以使用各种工具来帮助用户。",
    },
    "llm": {
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "provider": "deepseek",
    },
    "plugins": {
        "enabled": True,
        "builtin_path": "miniclaw.builtins",
    },
    "hooks": {
        "enabled": True,
    },
}


@dataclass
class MiniClawConfig:
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8003
    gateway_debug: bool = False
    agent_model: str = "deepseek-chat"
    agent_temperature: float = 0.7
    agent_max_tokens: int = 2048
    agent_max_tool_calls: int = 5
    agent_system_prompt: str = DEFAULT_CONFIG["agent"]["system_prompt"]
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_provider: str = "deepseek"
    plugins_enabled: bool = True
    hooks_enabled: bool = True
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MiniClawConfig":
        gw = data.get("gateway", {})
        ag = data.get("agent", {})
        llm = data.get("llm", {})
        pl = data.get("plugins", {})
        hk = data.get("hooks", {})
        return cls(
            gateway_host=gw.get("host", "0.0.0.0"),
            gateway_port=int(gw.get("port", 8003)),
            gateway_debug=gw.get("debug", False),
            agent_model=ag.get("model", "deepseek-chat"),
            agent_temperature=float(ag.get("temperature", 0.7)),
            agent_max_tokens=int(ag.get("max_tokens", 2048)),
            agent_max_tool_calls=int(ag.get("max_tool_calls", 5)),
            agent_system_prompt=ag.get("system_prompt", DEFAULT_CONFIG["agent"]["system_prompt"]),
            llm_api_key=llm.get("api_key", ""),
            llm_base_url=llm.get("base_url", "https://api.deepseek.com/v1"),
            llm_provider=llm.get("provider", "deepseek"),
            plugins_enabled=pl.get("enabled", True),
            hooks_enabled=hk.get("enabled", True),
            _raw=data,
        )

    @classmethod
    def from_env(cls) -> "MiniClawConfig":
        data = {}
        for key in ("MINICLAW_API_KEY", "DEEPSEEK_API_KEY"):
            val = os.getenv(key, "")
            if val:
                data.setdefault("llm", {})["api_key"] = val
        for key in ("MINICLAW_BASE_URL", "DEEPSEEK_BASE_URL"):
            val = os.getenv(key, "")
            if val:
                data.setdefault("llm", {})["base_url"] = val
        if os.getenv("MINICLAW_PORT"):
            data.setdefault("gateway", {})["port"] = int(os.getenv("MINICLAW_PORT"))
        if os.getenv("MINICLAW_HOST"):
            data.setdefault("gateway", {})["host"] = os.getenv("MINICLAW_HOST")
        return cls.from_dict(data)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "MiniClawConfig":
        config = dict(DEFAULT_CONFIG)
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                config = _deep_merge(config, user_config)
                logger.info(f"配置已从 {config_path} 加载")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        env_config = cls.from_env()
        merged = _deep_merge(config, env_config._raw)
        return cls.from_dict(merged)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gateway": {
                "host": self.gateway_host,
                "port": self.gateway_port,
                "debug": self.gateway_debug,
            },
            "agent": {
                "model": self.agent_model,
                "temperature": self.agent_temperature,
                "max_tokens": self.agent_max_tokens,
                "max_tool_calls": self.agent_max_tool_calls,
                "system_prompt": self.agent_system_prompt,
            },
            "llm": {
                "api_key": "***" if self.llm_api_key else "",
                "base_url": self.llm_base_url,
                "provider": self.llm_provider,
            },
            "plugins": {"enabled": self.plugins_enabled},
            "hooks": {"enabled": self.hooks_enabled},
        }


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
