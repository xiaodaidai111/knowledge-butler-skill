import os
import re
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    CHAT = "chat"
    GENERATE_IMAGE = "generate_image"
    ANALYZE_IMAGE = "analyze_image"
    HEALTH_INFO = "health_info"
    RECIPE = "recipe"


class ToolConfig(BaseModel):
    name: str
    description: str
    enabled: bool = True
    handler: Optional[Callable] = None


class TuantuanAgentConfig(BaseModel):
    chat_model_name: str = "qwen-plus"
    chat_api_key: Optional[str] = None
    chat_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    chat_temperature: float = 0.7

    vision_model_name: str = "qwen-vl-plus"
    vision_api_key: Optional[str] = None
    vision_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    image_model_name: str = "qwen-image-2.0"
    image_api_key: Optional[str] = None

    max_history_turns: int = 20
    conversation_timeout: int = 3600
    cleanup_interval: int = 300


class Conversation:
    def __init__(self, conversation_id: Optional[str] = None):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.turns: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.max_turns = 20
        self.timeout = 3600

    def add_turn(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        if self.is_timeout():
            raise ValueError("Conversation timed out")
        if len(self.turns) >= self.max_turns:
            self.turns.pop(0)
        turn = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.turns.append(turn)
        self.last_activity_time = datetime.now()
        return turn

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return self.turns[-limit:] if limit else self.turns

    def is_timeout(self) -> bool:
        return (datetime.now() - self.last_activity_time).total_seconds() > self.timeout


class ConversationManager:
    def __init__(self, max_turns: int = 20, timeout: int = 3600, cleanup_interval: int = 300):
        self.conversations: Dict[str, Conversation] = {}
        self._max_turns = max_turns
        self._timeout = timeout
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    def create_conversation(self, conversation_id: Optional[str] = None) -> str:
        conv = Conversation(conversation_id)
        conv.max_turns = self._max_turns
        conv.timeout = self._timeout
        self.conversations[conv.conversation_id] = conv
        self._cleanup()
        return conv.conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        conv = self.conversations.get(conversation_id)
        if conv and conv.is_timeout():
            del self.conversations[conversation_id]
            return None
        self._cleanup()
        return conv

    def add_message(self, conversation_id: str, role: str, content: str,
                    metadata: Optional[Dict[str, Any]] = None):
        conv = self.get_conversation(conversation_id)
        if not conv:
            return None
        try:
            return conv.add_turn(role, content, metadata)
        except ValueError:
            del self.conversations[conversation_id]
            return None

    def get_history(self, conversation_id: str, limit: Optional[int] = None):
        conv = self.get_conversation(conversation_id)
        if not conv:
            return None
        return conv.get_history(limit)

    def _cleanup(self):
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        expired = [cid for cid, c in self.conversations.items() if c.is_timeout()]
        for cid in expired:
            del self.conversations[cid]
        self._last_cleanup = now


class IntentAnalyzer:
    def __init__(self):
        self._image_gen_keywords = [
            '生成图片', '画图', '产图', '画一张', '生成一张', '画一个', '生成一个',
            '帮我画', '帮我生成', '画个', '生成个', '给我生成', '帮我生成一张',
            '帮我画一张', '生成一张关于', '画一张关于', '生成一个关于', '画一个关于',
            '生成图片', '画图片', '画个图片', '生成个图片', '画出来', '生成出来',
            '帮我画出来', '帮我生成出来', '生成一张画', '生成一张图', '画一幅',
            '生成一幅', '帮我画一幅', '帮我生成一幅',
        ]
        self._image_analysis_keywords = [
            '识别图片', '识图', '看图', '分析图片', '图片分析', '图片识别',
            '帮我识别', '识别这张', '这是什么菜', '这是什么食物',
        ]
        self._health_keywords = [
            '健康知识', '健康建议', '饮食健康', '运动健康', '睡眠健康',
            '心理健康', '疾病预防', '养生知识', '营养知识', '锻炼方法',
        ]

    def analyze(self, message: str, has_image: bool = False) -> IntentType:
        if not message:
            return IntentType.CHAT

        message_clean = re.sub(r'\s+', '', message)

        if has_image:
            return IntentType.ANALYZE_IMAGE

        for kw in self._image_gen_keywords:
            if kw in message or kw.replace(' ', '') in message_clean:
                return IntentType.GENERATE_IMAGE

        for kw in self._image_analysis_keywords:
            if kw in message or kw.replace(' ', '') in message_clean:
                return IntentType.ANALYZE_IMAGE

        for kw in self._health_keywords:
            if kw in message or kw.replace(' ', '') in message_clean:
                return IntentType.HEALTH_INFO

        return IntentType.CHAT


class ImageGenerator:
    def __init__(self, api_key: str, model_name: str = "qwen-image-2.0"):
        self.api_key = api_key
        self.model_name = model_name

    def generate(self, prompt: str, n: int = 1, watermark: bool = False,
                 negative_prompt: str = "") -> Dict[str, Any]:
        from dashscope import MultiModalConversation

        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]

        response = MultiModalConversation.call(
            api_key=self.api_key,
            model=self.model_name,
            messages=messages,
            result_format='message',
            stream=False,
            n=n,
            watermark=watermark,
            negative_prompt=negative_prompt
        )

        if response.status_code == 200:
            result = response.output.choices[0].message.content
            image_urls = self._extract_image_urls(result)
            if image_urls:
                return {
                    "success": True,
                    "image_urls": image_urls,
                    "prompt": prompt,
                }
            else:
                return {
                    "success": False,
                    "error": f"Image generation returned no URL. Raw: {result}"
                }
        else:
            return {
                "success": False,
                "error": response.message
            }

    def _extract_image_urls(self, result) -> List[str]:
        urls = []
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    url = item.get('url') or item.get('image')
                    if url:
                        urls.append(url)
                elif isinstance(item, str) and item.startswith('http'):
                    urls.append(item)
        elif isinstance(result, dict):
            url = result.get('url') or result.get('image')
            if url:
                urls.append(url)
        elif isinstance(result, str) and result.startswith('http'):
            urls.append(result)
        return urls


class VisionAnalyzer:
    def __init__(self, api_key: str, model_name: str = "qwen-vl-plus",
                 base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url

    def analyze(self, image_url: str = None, image_base64: str = None,
                prompt: str = "请评价这道美食") -> Dict[str, Any]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        system_prompt = (
            "你是一位专业的美食评价专家，名字叫团团。请对用户上传的美食图片进行评价，包括:\n"
            "1. 食材识别:识别图片中的主要食材\n"
            "2. 菜品分析:分析菜品的烹饪技巧、摆盘、色彩搭配等\n"
            "3. 评分:给出1-10分的评分(10分为最高分)\n"
            "4. 建议:给出改进建议或赞美\n\n"
            "请以JSON格式返回结果，格式如下:\n"
            "{\n"
            '    "ingredients": ["食材1", "食材2"],\n'
            '    "analysis": "菜品分析描述",\n'
            '    "score": 8.5,\n'
            '    "suggestion": "改进建议或赞美",\n'
            '    "exp_reward": 15\n'
            "}\n\n"
            "评分标准:\n"
            "- 9-10分:色香味俱全,摆盘精美,烹饪技巧高超\n"
            "- 7-8分:味道不错,摆盘良好,有一定创意\n"
            "- 5-6分:基本合格,但还有提升空间\n"
            "- 1-4分:需要改进\n\n"
            "经验值奖励规则:\n"
            "- 9-10分:奖励25经验值\n"
            "- 7-8分:奖励20经验值\n"
            "- 5-6分:奖励15经验值\n"
            "- 1-4分:奖励10经验值"
        )

        messages = [{"role": "system", "content": system_prompt}]

        user_content = []
        if image_url:
            user_content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_base64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            })
        user_content.append({"type": "text", "text": prompt})
        messages.append({"role": "user", "content": user_content})

        completion = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )

        if completion and completion.choices and len(completion.choices) > 0:
            response_text = completion.choices[0].message.content
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "ingredients": [],
                    "analysis": response_text,
                    "score": 5.0,
                    "suggestion": "",
                    "exp_reward": 10
                }
        return {"error": "No response from model"}


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolConfig] = {}

    def register(self, name: str, description: str, handler: Callable, enabled: bool = True):
        self._tools[name] = ToolConfig(
            name=name, description=description, enabled=enabled, handler=handler
        )

    def get(self, name: str) -> Optional[ToolConfig]:
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, ToolConfig]:
        return {k: v for k, v in self._tools.items() if v.enabled}

    def execute(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool or not tool.enabled:
            raise ValueError(f"Tool '{name}' not found or disabled")
        return tool.handler(**kwargs)


class TuantuanAgent:
    def __init__(self, config: Optional[TuantuanAgentConfig] = None):
        self.config = config or self._default_config()
        self.conversation_manager = ConversationManager(
            max_turns=self.config.max_history_turns,
            timeout=self.config.conversation_timeout,
            cleanup_interval=self.config.cleanup_interval
        )
        self.intent_analyzer = IntentAnalyzer()
        self.tool_registry = ToolRegistry()

        self._chat_llm = None
        self._image_generator = None
        self._vision_analyzer = None

        self._init_tools()
        self._init_components()

    @staticmethod
    def _default_config() -> TuantuanAgentConfig:
        dashscope_key = (
            os.getenv('DASHSCOPE_API_KEY_TUANTUAN')
            or os.getenv('DASHSCOPE_API_KEY')
            or os.getenv('QWEN_API_KEY')
            or ''
        )
        return TuantuanAgentConfig(
            chat_model_name=os.getenv('QWEN_MODEL', 'qwen-plus'),
            chat_api_key=dashscope_key,
            chat_base_url=os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            vision_model_name=os.getenv('QWEN_VISION_MODEL', 'qwen-vl-plus'),
            vision_api_key=dashscope_key,
            vision_base_url=os.getenv('QWEN_VISION_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            image_model_name=os.getenv('QWEN_IMAGE_MODEL', 'qwen-image-2.0'),
            image_api_key=dashscope_key,
        )

    def _init_tools(self):
        self.tool_registry.register(
            name="generate_image",
            description="使用千问文生图模型生成图片",
            handler=self._tool_generate_image
        )
        self.tool_registry.register(
            name="analyze_image",
            description="使用视觉模型分析美食图片",
            handler=self._tool_analyze_image
        )
        self.tool_registry.register(
            name="chat",
            description="与用户进行烹饪相关的对话",
            handler=self._tool_chat
        )

    def _init_components(self):
        if self.config.chat_api_key:
            self._chat_llm = ChatOpenAI(
                model=self.config.chat_model_name,
                temperature=self.config.chat_temperature,
                api_key=self.config.chat_api_key,
                base_url=self.config.chat_base_url
            )
        if self.config.image_api_key:
            self._image_generator = ImageGenerator(
                api_key=self.config.image_api_key,
                model_name=self.config.image_model_name
            )
        if self.config.vision_api_key:
            self._vision_analyzer = VisionAnalyzer(
                api_key=self.config.vision_api_key,
                model_name=self.config.vision_model_name,
                base_url=self.config.vision_base_url
            )

    def _get_system_prompt(self) -> str:
        return (
            "你是智学问修助手，一位专业的设备检修技术顾问。你的核心功能包括：\n"
            "1. 故障诊断：根据用户描述的故障现象，分析可能原因并给出排查步骤\n"
            "2. 检修指导：提供标准化的检修作业流程、工具清单和安全注意事项\n"
            "3. 知识解答：解答设备结构、原理、维护保养的专业问题\n"
            "4. 案例分析：基于历史检修案例，提供类似故障的处理经验\n"
            "5. 安全提醒：强调检修作业中的安全防护措施和合规要求\n\n"
            "重要要求：\n"
            "- 回答内容要具备实际可操作性，优先给出具体的排查步骤和检修方法\n"
            "- 涉及安全操作时（如停电验电、挂牌上锁等），必须明确提醒安全防护措施\n"
            "- 对于复杂故障，按概率从高到低列出可能原因\n"
            "- 保持回答的专业性和实用性\n"
            "- 语言要通俗易懂，一线检修人员能理解\n"
            "- 回复不得采用Markdown格式，应直接呈现文本内容\n"
            "- 回复内容需具备清晰的结构和段落划分"
        )

    def _build_langchain_messages(self, conversation_id: str,
                                  user_message: str) -> List:
        system_prompt = self._get_system_prompt()
        messages = [SystemMessage(content=system_prompt)]

        history = self.conversation_manager.get_history(conversation_id, limit=10)
        if history:
            for turn in history:
                if turn['role'] == 'user':
                    messages.append(HumanMessage(content=turn['content']))
                elif turn['role'] == 'assistant':
                    messages.append(AIMessage(content=turn['content']))

        messages.append(HumanMessage(content=user_message))
        return messages

    def _tool_chat(self, message: str, conversation_id: str,
                   user_prefs: str = "") -> Dict[str, Any]:
        if not self._chat_llm:
            return {
                "type": "chat",
                "content": "抱歉，团团的AI服务暂时不可用，请检查API配置。"
            }

        langchain_messages = self._build_langchain_messages(conversation_id, message)
        if user_prefs:
            langchain_messages[0] = SystemMessage(
                content=self._get_system_prompt() + "\n\n" + user_prefs
            )

        response = self._chat_llm.invoke(langchain_messages)
        content = response.content

        if "think" in content.lower() and "\u2764\ufe0f" in content:
            pass

        if "\U0001f9e0" in content:
            think_match = re.search(r'\U0001f9e0(.*?)\U0001f4a4', content, re.DOTALL)
            if think_match:
                content = re.sub(r'\U0001f9e0.*?\U0001f4a4', '', content,
                                 flags=re.DOTALL).strip()

        return {
            "type": "chat",
            "content": content.strip()
        }

    def _tool_generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self._image_generator:
            return {
                "type": "chat",
                "content": "抱歉，图片生成服务暂时不可用，请检查API配置。"
            }

        optimized_prompt = (
            f"高质量、清晰、详细的美食图片，展示{prompt}，"
            f"光线自然，色彩鲜艳，构图美观，食物看起来令人食欲大开"
        )

        result = self._image_generator.generate(optimized_prompt)
        if result.get("success"):
            return {
                "type": "image_generation",
                "content": {
                    "image_url": result["image_urls"][0],
                    "prompt": prompt,
                    "optimized_prompt": optimized_prompt,
                    "status": "success"
                }
            }
        else:
            return {
                "type": "chat",
                "content": f"抱歉，图片生成失败：{result.get('error', '未知错误')}"
            }

    def _tool_analyze_image(self, image_url: str = None, image_base64: str = None,
                            **kwargs) -> Dict[str, Any]:
        if not self._vision_analyzer:
            return {
                "type": "chat",
                "content": "抱歉，图片分析服务暂时不可用，请检查API配置。"
            }

        result = self._vision_analyzer.analyze(
            image_url=image_url, image_base64=image_base64
        )
        if "error" in result:
            return {
                "type": "chat",
                "content": f"图片分析失败：{result['error']}"
            }
        return {
            "type": "image_analysis",
            "content": result
        }

    def process_message(self, conversation_id: str, message: str,
                        image_url: str = None, image_base64: str = None,
                        uploaded_file: str = None,
                        user_prefs: str = "") -> Dict[str, Any]:
        if not conversation_id:
            conversation_id = self.conversation_manager.create_conversation()

        if not self.conversation_manager.get_conversation(conversation_id):
            conversation_id = self.conversation_manager.create_conversation()

        self.conversation_manager.add_message(
            conversation_id, 'user', message,
            {'type': 'user_input'}
        )

        has_image = bool(image_url or image_base64 or uploaded_file)
        intent = self.intent_analyzer.analyze(message, has_image)

        thinking_steps = [
            {"type": "thought", "step": "接收消息",
             "content": f"用户输入: {message[:100]}"},
            {"type": "thought", "step": "意图识别",
             "content": f"识别意图: {intent.value}"}
        ]

        try:
            if intent == IntentType.GENERATE_IMAGE:
                thinking_steps.append({
                    "type": "action", "step": "调用文生图",
                    "content": f"模型: {self.config.image_model_name}"
                })
                result = self._tool_generate_image(prompt=message)
                thinking_steps.append({
                    "type": "observation", "step": "文生图完成",
                    "content": "成功" if result.get("type") == "image_generation" else "失败"
                })

            elif intent == IntentType.ANALYZE_IMAGE:
                actual_image_url = image_url or (uploaded_file if uploaded_file else None)
                thinking_steps.append({
                    "type": "action", "step": "调用视觉分析",
                    "content": f"模型: {self.config.vision_model_name}"
                })
                result = self._tool_analyze_image(image_url=actual_image_url,
                                                  image_base64=image_base64)
                thinking_steps.append({
                    "type": "observation", "step": "图片分析完成",
                    "content": "成功" if result.get("type") == "image_analysis" else "失败"
                })

            else:
                thinking_steps.append({
                    "type": "action", "step": "调用对话模型",
                    "content": f"模型: {self.config.chat_model_name}"
                })
                result = self._tool_chat(
                    message=message,
                    conversation_id=conversation_id,
                    user_prefs=user_prefs
                )
                thinking_steps.append({
                    "type": "observation", "step": "对话完成",
                    "content": "成功获取回复"
                })

            response_content = ""
            if result.get("type") == "image_generation":
                response_content = f"[已为您生成图片: {message}]"
            elif result.get("type") == "image_analysis":
                analysis = result.get("content", {})
                response_content = f"[图片分析完成，评分: {analysis.get('score', 'N/A')}]"
            else:
                response_content = result.get("content", "")

            self.conversation_manager.add_message(
                conversation_id, 'assistant', response_content,
                {'type': result.get("type", "chat"), 'thinking_process': thinking_steps}
            )

            result["conversation_id"] = conversation_id
            result["thinking_process"] = thinking_steps
            return result

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_msg = f"抱歉，处理您的请求时出现错误: {str(e)}"
            self.conversation_manager.add_message(
                conversation_id, 'assistant', error_msg,
                {'type': 'error', 'thinking_process': thinking_steps}
            )
            return {
                "type": "chat",
                "content": error_msg,
                "conversation_id": conversation_id,
                "thinking_process": thinking_steps
            }

    def create_conversation(self) -> str:
        return self.conversation_manager.create_conversation()

    def get_conversation_history(self, conversation_id: str,
                                 limit: int = 20) -> Optional[List]:
        return self.conversation_manager.get_history(conversation_id, limit)

    def register_tool(self, name: str, description: str, handler: Callable,
                      enabled: bool = True):
        self.tool_registry.register(name, description, handler, enabled)

    def list_available_tools(self) -> Dict[str, str]:
        return {
            name: tool.description
            for name, tool in self.tool_registry.list_tools().items()
        }


tuantuan_agent = TuantuanAgent()
