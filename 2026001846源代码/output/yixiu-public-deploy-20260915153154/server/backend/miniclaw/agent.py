"""MiniClaw Agent 引擎

模仿 OpenClaw 的 agents/ 模块，实现 ReAct (Reasoning + Acting) 循环。
Agent 通过 LLM 推理决定是否调用工具，执行工具后继续推理，直到生成最终回答。
"""
import json
import re
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .config import MiniClawConfig
from .tools import ToolRegistry, ToolResult, global_tool_registry
from .hooks import HookRunner, global_hook_runner

logger = logging.getLogger("miniclaw.agent")


@dataclass
class AgentStep:
    step_type: str
    content: str = ""
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    tool_result: Optional[ToolResult] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.step_type, "content": self.content}
        if self.tool_name:
            result["tool"] = self.tool_name
            result["args"] = self.tool_args
        if self.tool_result:
            result["tool_result"] = {
                "success": self.tool_result.success,
                "output": self.tool_result.output,
                "error": self.tool_result.error,
            }
        return result


@dataclass
class AgentResponse:
    reply: str
    steps: List[AgentStep] = field(default_factory=list)
    tool_calls: int = 0
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tool_calls": self.tool_calls,
            "success": self.success,
            "error": self.error,
        }


class MiniClawAgent:
    def __init__(
        self,
        config: Optional[MiniClawConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
        hook_runner: Optional[HookRunner] = None,
    ):
        self.config = config or MiniClawConfig.from_env()
        self.tools = tool_registry or global_tool_registry
        self.hooks = hook_runner or global_hook_runner
        self._llm_client = None

    def _get_llm_client(self):
        """复用统一 AI 网关 (services.ai_gateway.ai_agent)。

        优先使用项目已配置的 qwen/deepseek 网关，避免 miniclaw 单独维护一套 LLM 配置。
        """
        if self._llm_client is not None:
            return self._llm_client
        try:
            from services.ai_gateway import ai_agent
            if not ai_agent.settings.configured:
                logger.warning("AI 网关未配置 API Key，请在 server/backend/.env 设置 DASHSCOPE_API_KEY 等")
                return None
            self._llm_client = ai_agent.client()
            return self._llm_client
        except Exception as exc:  # noqa: BLE001
            logger.error("获取 AI 网关客户端失败: %s", exc)
            return None

    def _resolve_model(self) -> str:
        """解析实际使用的模型：若 config 仍是默认 deepseek-chat，则回退到网关配置的模型。"""
        if self.config.agent_model and self.config.agent_model != "deepseek-chat":
            return self.config.agent_model
        try:
            from services.ai_gateway import ai_agent
            if ai_agent.settings.chat_model:
                return ai_agent.settings.chat_model
        except Exception:  # noqa: BLE001
            pass
        return self.config.agent_model

    def _build_system_prompt(self) -> str:
        base = self.config.agent_system_prompt
        if self.tools:
            tools_desc = self.tools.get_tools_description()
            base += f"\n\n## 可用工具\n{tools_desc}\n\n## 工具调用规则\n"
            base += "- 当用户的问题需要使用工具时，请按以下格式调用工具：\n"
            base += "  [TOOL_CALL]工具名称|参数JSON[/TOOL_CALL]\n"
            base += "- 例如: [TOOL_CALL]calculator|{\"expression\": \"2+3*4\"}[/TOOL_CALL]\n"
            base += "- 你可以在一次回复中调用多个工具\n"
            base += "- 调用工具后，根据工具返回的结果继续回答用户\n"
            base += "- 如果不需要工具，直接回答即可\n"
        return base

    def _parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        pattern = r'\[TOOL_CALL\](\w+)\|(.+?)\[/TOOL_CALL\]'
        matches = re.findall(pattern, text, re.DOTALL)
        calls = []
        for tool_name, args_str in matches:
            try:
                args = json.loads(args_str.strip())
                calls.append({"tool": tool_name, "args": args})
            except json.JSONDecodeError:
                calls.append({"tool": tool_name, "args": {"raw": args_str.strip()}})
        return calls

    def _remove_tool_calls_from_text(self, text: str) -> str:
        return re.sub(r'\[TOOL_CALL\].+?\[/TOOL_CALL\]', '', text, flags=re.DOTALL).strip()

    def _call_llm(self, messages: List[Dict[str, str]]) -> Optional[str]:
        client = self._get_llm_client()
        if not client:
            return None
        try:
            self.hooks.emit_sync("before_llm_call", {"messages": messages})
            response = client.chat.completions.create(
                model=self._resolve_model(),
                messages=messages,
                temperature=self.config.agent_temperature,
                max_tokens=self.config.agent_max_tokens,
                stream=False,
            )
            content = response.choices[0].message.content
            self.hooks.emit_sync("after_llm_call", {"response": content})
            return content
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return None

    def process(self, message: str, conversation_id: str = "default") -> AgentResponse:
        import datetime
        steps: List[AgentStep] = []
        tool_call_count = 0

        self.hooks.emit_sync("message_received", {
            "message": message,
            "conversation_id": conversation_id,
        })

        self.hooks.emit_sync("before_agent_start", {
            "message": message,
            "conversation_id": conversation_id,
        })

        client = self._get_llm_client()
        if not client:
            return AgentResponse(
                reply="AI 未连接，请检查 LLM API 配置。",
                steps=steps,
                success=False,
                error="LLM client not available",
            )

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": message},
        ]

        max_iterations = self.config.agent_max_tool_calls + 1
        final_reply = ""

        for iteration in range(max_iterations):
            llm_response = self._call_llm(messages)
            if not llm_response:
                final_reply = "AI 调用失败，请稍后重试。"
                break

            tool_calls = self._parse_tool_calls(llm_response)
            clean_text = self._remove_tool_calls_from_text(llm_response)

            if not tool_calls:
                final_reply = clean_text or llm_response
                steps.append(AgentStep(
                    step_type="thought",
                    content=final_reply[:200],
                    timestamp=datetime.datetime.now().isoformat(),
                ))
                break

            steps.append(AgentStep(
                step_type="action",
                content=f"检测到 {len(tool_calls)} 个工具调用",
                timestamp=datetime.datetime.now().isoformat(),
            ))

            tool_results_text = []
            for call in tool_calls:
                tool_name = call["tool"]
                tool_args = call["args"]

                self.hooks.emit_sync("before_tool_call", {
                    "tool": tool_name,
                    "args": tool_args,
                })

                result = self.tools.call(tool_name, **tool_args)
                tool_call_count += 1

                self.hooks.emit_sync("after_tool_call", {
                    "tool": tool_name,
                    "result": {"success": result.success, "output": result.output, "error": result.error},
                })

                steps.append(AgentStep(
                    step_type="tool_call",
                    content=f"调用工具: {tool_name}",
                    tool_name=tool_name,
                    tool_args=tool_args,
                    tool_result=result,
                    timestamp=datetime.datetime.now().isoformat(),
                ))

                result_str = result.output if result.success else f"错误: {result.error}"
                tool_results_text.append(f"工具 {tool_name} 返回: {result_str}")

            messages.append({"role": "assistant", "content": llm_response})
            messages.append({
                "role": "user",
                "content": f"工具执行结果:\n" + "\n".join(tool_results_text) + "\n\n请根据以上工具结果回答用户。",
            })

        self.hooks.emit_sync("after_agent_start", {
            "reply": final_reply,
            "tool_calls": tool_call_count,
            "conversation_id": conversation_id,
        })

        self.hooks.emit_sync("message_sent", {
            "reply": final_reply,
            "conversation_id": conversation_id,
        })

        return AgentResponse(
            reply=final_reply,
            steps=steps,
            tool_calls=tool_call_count,
            success=True,
        )
