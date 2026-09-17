"""统一 AI Agent 网关。

本模块把系统内文本对话、图片理解、向量化和图片生成的模型配置收拢到
一个入口。业务层不再直接关心 DeepSeek / Qwen / OpenAI 的密钥和 base_url。
"""
from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=False)


def _env_first(*keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return default


@dataclass(frozen=True)
class AIModelSettings:
    provider: str
    api_key: str
    base_url: str
    chat_model: str
    vision_model: str
    embedding_model: str
    image_model: str
    timeout: int = 45

    @property
    def configured(self) -> bool:
        return bool(self.api_key)


def load_ai_settings() -> AIModelSettings:
    provider = _env_first("AI_PROVIDER", default="qwen").lower()

    if provider in {"qwen", "dashscope", "aliyun"}:
        api_key = _env_first("DASHSCOPE_API_KEY_TUANTUAN", "DASHSCOPE_API_KEY", "QWEN_API_KEY")
        base_url = _env_first("QWEN_BASE_URL", default="https://dashscope.aliyuncs.com/compatible-mode/v1")
        return AIModelSettings(
            provider="qwen",
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            chat_model=_env_first("QWEN_MODEL", default="qwen-plus"),
            vision_model=_env_first("QWEN_VISION_MODEL", "QWEN_IMAGE_MODEL", default="qwen-vl-plus"),
            embedding_model=_env_first("EMBEDDING_MODEL", "QWEN_EMBEDDING_MODEL", default="text-embedding-v4"),
            image_model=_env_first("QWEN_IMAGE_MODEL", default="qwen-image-2.0"),
            timeout=int(_env_first("AI_TIMEOUT", "QWEN_TIMEOUT", default="45")),
        )

    if provider == "deepseek":
        return AIModelSettings(
            provider="deepseek",
            api_key=_env_first("DEEPSEEK_API_KEY"),
            base_url=_env_first("DEEPSEEK_BASE_URL", default="https://api.deepseek.com").rstrip("/"),
            chat_model=_env_first("DEEPSEEK_CHAT_MODEL", "DEEPSEEK_MODEL_NAME", default="deepseek-v4-flash"),
            vision_model=_env_first("QWEN_VISION_MODEL", default="qwen-vl-plus"),
            embedding_model=_env_first("EMBEDDING_MODEL", default="text-embedding-v4"),
            image_model=_env_first("QWEN_IMAGE_MODEL", default="qwen-image-2.0"),
            timeout=int(_env_first("AI_TIMEOUT", "DEEPSEEK_TIMEOUT", default="45")),
        )

    return AIModelSettings(
        provider="openai",
        api_key=_env_first("OPENAI_API_KEY"),
        base_url=_env_first("OPENAI_BASE_URL", default="https://api.openai.com/v1").rstrip("/"),
        chat_model=_env_first("OPENAI_CHAT_MODEL", default="gpt-4o-mini"),
        vision_model=_env_first("OPENAI_VISION_MODEL", default="gpt-4o-mini"),
        embedding_model=_env_first("OPENAI_EMBEDDING_MODEL", default="text-embedding-3-small"),
        image_model=_env_first("OPENAI_IMAGE_MODEL", default="gpt-image-1"),
        timeout=int(_env_first("AI_TIMEOUT", "OPENAI_TIMEOUT", default="45")),
    )


class UnifiedAIAgent:
    """基于 OpenAI 兼容协议的统一 Agent 能力层。"""

    def __init__(self, settings: Optional[AIModelSettings] = None):
        self.settings = settings or load_ai_settings()
        self._client = None
        self._async_client = None

    def status(self) -> Dict[str, Any]:
        return {
            "provider": self.settings.provider,
            "configured": self.settings.configured,
            "base_url": self.settings.base_url,
            "chat_model": self.settings.chat_model,
            "vision_model": self.settings.vision_model,
            "embedding_model": self.settings.embedding_model,
            "image_model": self.settings.image_model,
        }

    def client(self):
        if not self.settings.configured:
            return None
        if self._client is None:
            import httpx
            from openai import OpenAI

            trust_env = os.getenv("AI_TRUST_ENV", "0").strip() == "1"
            self._client = OpenAI(
                api_key=self.settings.api_key,
                base_url=self.settings.base_url,
                http_client=httpx.Client(trust_env=trust_env, timeout=self.settings.timeout),
            )
        return self._client

    def async_client(self):
        if not self.settings.configured:
            return None
        if self._async_client is None:
            import httpx
            from openai import AsyncOpenAI

            trust_env = os.getenv("AI_TRUST_ENV", "0").strip() == "1"
            self._async_client = AsyncOpenAI(
                api_key=self.settings.api_key,
                base_url=self.settings.base_url,
                http_client=httpx.AsyncClient(trust_env=trust_env, timeout=self.settings.timeout),
            )
        return self._async_client

    def langchain_chat(self, model: Optional[str] = None, temperature: float = 0.7):
        if not self.settings.configured:
            return None
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or self.settings.chat_model,
            temperature=temperature,
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
        )

    def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **extra: Any,
    ) -> str:
        client = self.client()
        if client is None:
            raise RuntimeError("AI API key is not configured")
        payload: Dict[str, Any] = {
            "model": model or self.settings.chat_model,
            "messages": list(messages),
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(extra)
        response = client.chat.completions.create(**payload)
        return self._extract_text(response)

    async def async_chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **extra: Any,
    ) -> str:
        client = self.async_client()
        if client is None:
            raise RuntimeError("AI API key is not configured")
        payload: Dict[str, Any] = {
            "model": model or self.settings.chat_model,
            "messages": list(messages),
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(extra)
        response = await client.chat.completions.create(**payload)
        return self._extract_text(response)

    def vision(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        system_prompt: str = "你是专业的多模态分析助手，请给出准确、结构化的中文分析。",
        model: Optional[str] = None,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:
        content: List[Dict[str, Any]] = []
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        if image_base64:
            url = image_base64
            if not image_base64.startswith("data:image"):
                url = f"data:image/jpeg;base64,{image_base64}"
            content.append({"type": "image_url", "image_url": {"url": url}})
        content.append({"type": "text", "text": prompt})

        extra: Dict[str, Any] = {}
        if json_mode:
            extra["response_format"] = {"type": "json_object"}
        return self.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            model=model or self.settings.vision_model,
            temperature=temperature,
            **extra,
        )

    def embeddings(self, texts: Iterable[str], model: Optional[str] = None) -> List[List[float]]:
        client = self.client()
        if client is None:
            raise RuntimeError("AI API key is not configured")
        response = client.embeddings.create(model=model or self.settings.embedding_model, input=list(texts))
        return [item.embedding for item in response.data]

    async def async_embeddings(self, texts: Iterable[str], model: Optional[str] = None) -> List[List[float]]:
        client = self.async_client()
        if client is None:
            raise RuntimeError("AI API key is not configured")
        response = await client.embeddings.create(model=model or self.settings.embedding_model, input=list(texts))
        return [item.embedding for item in response.data]

    def generate_image(self, prompt: str, model: Optional[str] = None) -> List[str]:
        """调用百炼多模态接口生成图片，返回 URL 列表。"""
        api_key = self.settings.api_key
        if not api_key:
            raise RuntimeError("AI API key is not configured")
        from dashscope import MultiModalConversation

        response = MultiModalConversation.call(
            api_key=api_key,
            model=model or self.settings.image_model,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            result_format="message",
            stream=False,
            n=1,
            watermark=False,
        )
        if getattr(response, "status_code", None) != 200:
            raise RuntimeError(getattr(response, "message", "image generation failed"))
        content = response.output.choices[0].message.content
        return self._extract_urls(content)

    @staticmethod
    def _extract_text(response: Any) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        message = choices[0].message
        content = getattr(message, "content", "")
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(str(item.get("text") or ""))
                    elif "text" in item:
                        parts.append(str(item.get("text") or ""))
            return "".join(parts).strip()
        return str(content or "").strip()

    @staticmethod
    def _extract_urls(content: Any) -> List[str]:
        urls: List[str] = []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("image")
                    if url:
                        urls.append(str(url))
                elif isinstance(item, str) and item.startswith("http"):
                    urls.append(item)
        elif isinstance(content, dict):
            url = content.get("url") or content.get("image")
            if url:
                urls.append(str(url))
        elif isinstance(content, str) and content.startswith("http"):
            urls.append(content)
        return urls

    @staticmethod
    def parse_json(text: str) -> Dict[str, Any]:
        cleaned = (text or "").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except Exception:
            logger.warning("AI response is not valid JSON: %s", cleaned[:200])
            return {}

    @staticmethod
    def image_bytes_to_base64(image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")


ai_agent = UnifiedAIAgent()
