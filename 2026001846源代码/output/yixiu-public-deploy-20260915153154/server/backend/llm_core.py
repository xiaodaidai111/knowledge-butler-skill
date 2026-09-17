import os
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from utils import Config
from services.ai_gateway import ai_agent

logger = logging.getLogger(__name__)

class APIKeyManager:
    def __init__(self):
        self._api_keys: Dict[str, str] = {}
        self._load_keys_from_env()
    
    def _load_keys_from_env(self):
        if Config.AMAP_API_KEY:
            self._api_keys["amap"] = Config.AMAP_API_KEY
        if Config.QWEN_API_KEY:
            self._api_keys["qwen"] = Config.QWEN_API_KEY
        if Config.DEEPSEEK_API_KEY:
            self._api_keys["deepseek"] = Config.DEEPSEEK_API_KEY
    
    def get_key(self, provider: str) -> Optional[str]:
        return self._api_keys.get(provider)
    
    def has_key(self, provider: str) -> bool:
        return provider in self._api_keys and bool(self._api_keys[provider])

api_key_manager = APIKeyManager()

class ModelInfo(BaseModel):
    name: str = Field(description="模型名称")
    provider: str = Field(description="提供商")
    version: str = Field(description="版本")
    max_tokens: int = Field(description="最大token数")
    supports_functions: bool = Field(default=True)

class ModelManager:
    MODELS = {
        "qwen-plus": ModelInfo(
            name="qwen-plus", provider="qwen", version="dashscope", max_tokens=8192, supports_functions=True
        ),
        "deepseek-chat": ModelInfo(
            name="deepseek-chat", provider="deepseek", version="1.0", max_tokens=4000, supports_functions=True
        )
    }
    
    def __init__(self):
        self._current_model: Optional[str] = ai_agent.settings.chat_model or "qwen-plus"
    
    def get_current_model(self) -> Optional[str]:
        return self._current_model

model_manager = ModelManager()

class _AIChatAdapter:
    def __init__(self, model_name: str, temperature: float):
        self.model_name = model_name
        self.temperature = temperature

    def invoke(self, langchain_messages):
        messages = []
        for item in langchain_messages:
            role = "user"
            item_type = getattr(item, "type", "")
            if item_type == "system" or item.__class__.__name__ == "SystemMessage":
                role = "system"
            elif item_type == "ai" or item.__class__.__name__ == "AIMessage":
                role = "assistant"
            messages.append({"role": role, "content": getattr(item, "content", str(item))})

        content = ai_agent.chat(
            messages=messages,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=2000,
        )

        class _Response:
            def __init__(self, content):
                self.content = content

        return _Response(content)


class LLMConfig(BaseModel):
    model_name: str = Field(default_factory=lambda: model_manager.get_current_model() or "qwen-plus", description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: str = Field(default_factory=lambda: ai_agent.settings.base_url, description="API基础URL")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.api_key = ai_agent.settings.api_key
        self.model_name = ai_agent.settings.chat_model
        self.base_url = ai_agent.settings.base_url
    
    def create_llm(self):
        if not ai_agent.settings.configured:
            return None
        return _AIChatAdapter(self.model_name, self.temperature)

llm_config = LLMConfig()

class PromptTemplateManager:
    SYSTEM_PROMPTS = {
        "default": """你是设备检修知识助手"智学"。你的交互界面是一个集成设备检修知识检索与标准作业指引的智能系统。

工作逻辑：
1. 分析用户的设备检修需求，包括故障现象、设备型号、检修等级等关键信息。
2. 从知识库中检索匹配的检修手册、标准作业流程和历史案例。
3. 提供结构化的检修指引，包括故障排查步骤、工具清单、安全注意事项和合规要求。

输出要求：
- 使用专业、准确的检修术语，同时确保一线人员易于理解
- 对于安全关键步骤（如停电验电、挂牌上锁等），必须明确标注并强调
- 回复内容需具备清晰的结构和段落划分，确保逻辑层次分明
- 回复不得采用Markdown格式，应直接呈现文本内容
- 始终将安全生产放在首位，涉及高风险操作时必须提醒安全防护措施
- 重点突出：故障现象、排查步骤、所需工具、安全注意事项、预计工时
- 如果涉及多个可能的故障原因，按概率从高到低排列
- 300字左右
"""
    }

    def __init__(self):
        self._knowledge_context = None

    def _load_knowledge_context(self):
        """懒加载知识库上下文"""
        if self._knowledge_context is None:
            try:
                from services.knowledge_retriever import build_context
                self._knowledge_context = build_context()
                if self._knowledge_context:
                    logger.info("知识库上下文已加载，长度: %d 字符", len(self._knowledge_context))
            except Exception as e:
                logger.warning("加载知识库上下文失败: %s", e)
                self._knowledge_context = ""
        return self._knowledge_context

    def get_prompt(self, prompt_name: str = "default") -> str:
        base = self.SYSTEM_PROMPTS.get(prompt_name, self.SYSTEM_PROMPTS["default"])
        kb_ctx = self._load_knowledge_context()
        if kb_ctx:
            return f"{base}\n\n以下是设备检修知识库的参考资料，请在回答时优先参考：\n\n{kb_ctx}"
        return base

    def get_relevant_context(self, query: str) -> str:
        """根据用户查询检索相关知识（用于动态上下文注入）"""
        try:
            from services.knowledge_retriever import retrieve
            return retrieve(query)
        except Exception:
            return ""

prompt_manager = PromptTemplateManager()

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
            raise ValueError("对话已超时")
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
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.cleanup_interval = 300
        self.last_cleanup = time.time()
    
    def create_conversation(self) -> str:
        conversation = Conversation()
        self.conversations[conversation.conversation_id] = conversation
        self._cleanup_timeout_conversations()
        return conversation.conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        conversation = self.conversations.get(conversation_id)
        if conversation and conversation.is_timeout():
            del self.conversations[conversation_id]
            return None
        self._cleanup_timeout_conversations()
        return conversation
    
    def add_message(self, conversation_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        try:
            return conversation.add_turn(role, content, metadata)
        except ValueError:
            del self.conversations[conversation_id]
            return None
    
    def get_conversation_history(self, conversation_id: str, limit: Optional[int] = None):
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        return conversation.get_history(limit)
    
    def _cleanup_timeout_conversations(self):
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        timeout_conversations = [cid for cid, conv in self.conversations.items() if conv.is_timeout()]
        for cid in timeout_conversations:
            del self.conversations[cid]
        self.last_cleanup = current_time

conversation_manager = ConversationManager()
