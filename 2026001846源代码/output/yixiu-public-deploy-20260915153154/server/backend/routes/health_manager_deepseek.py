import logging
import os
from typing import Any, Dict, List

import requests
from flask import Blueprint, jsonify, request
from services.ai_gateway import ai_agent

logger = logging.getLogger(__name__)

health_manager_bp = Blueprint("health_manager", __name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
DEEPSEEK_CHAT_MODEL = os.getenv(
    "DEEPSEEK_CHAT_MODEL",
    os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat"),
).strip()
DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "45"))

SYSTEM_PROMPT = """你是健康糖豆，一位温和、专业、易懂的中文健康助手。

你的任务：
1. 回答饮食、运动、体重管理、BMI、日常健康习惯相关问题。
2. 优先根据用户提供的上下文给出个性化建议。
3. 建议要具体、可执行，但不要使用医学诊断口吻。
4. 涉及疾病、药物、急症、高风险症状时，提醒用户及时线下就医。

回复要求：
1. 使用自然、简洁、鼓励式中文。
2. 不使用 markdown 标题或代码块。
3. 一般控制在 2 到 5 句话，必要时可分点但保持简洁。
"""


def _chat_endpoint(base_url: str) -> str:
    normalized = (base_url or "https://api.deepseek.com").rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/chat/completions"


def _normalize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for message in messages[-20:]:
        role = str(message.get("role") or "user").strip().lower()
        if role == "bot":
            role = "assistant"
        if role not in {"system", "user", "assistant"}:
            role = "user"

        content = str(message.get("content") or "").strip()
        if not content:
            continue

        normalized.append({"role": role, "content": content})
    return normalized


def _summarize_user_context(user_context: Dict[str, Any]) -> str:
    if not isinstance(user_context, dict):
        return ""

    profile = user_context.get("user")
    if isinstance(profile, dict):
        user_context = {**user_context, **profile}

    field_map = {
        "name": "用户昵称",
        "age": "年龄",
        "gender": "性别",
        "height": "身高",
        "weight": "体重",
        "bmi": "BMI",
        "goal": "健康目标",
        "allergies": "过敏信息",
        "disease_history": "既往病史",
        "dietary_preferences": "饮食偏好",
    }

    lines: List[str] = []
    for key, label in field_map.items():
        value = user_context.get(key)
        if value in (None, "", [], {}):
            continue
        lines.append(f"{label}: {value}")

    return "\n".join(lines)


def _fallback_reply(latest_user_message: str) -> str:
    text = latest_user_message.lower()
    if any(keyword in text for keyword in ("bmi", "体脂", "身高", "体重")):
        return "可以把你的身高和体重发给我，我来帮你快速判断 BMI 和体重状态，并给你饮食建议。"
    if any(keyword in text for keyword in ("减肥", "减脂", "瘦")):
        return "减脂最关键的是控制总热量、保证蛋白质、减少高糖高油零食，再配合规律运动和睡眠。你愿意的话，我可以按你的身高体重帮你做一版更具体的建议。"
    if any(keyword in text for keyword in ("吃什么", "饮食", "早餐", "午餐", "晚餐")):
        return "建议优先选择高蛋白、少油少糖、蔬菜充足的一餐，比如鸡蛋、瘦肉、豆制品、全谷物和绿叶菜的组合。告诉我你的目标，我可以继续帮你细化。"
    return "我在这儿，可以帮你看饮食、BMI、体重管理和运动安排。你把具体情况告诉我，我会尽量给你简单好用的建议。"


def _call_deepseek(messages: List[Dict[str, str]]) -> str:
    content = ai_agent.chat(messages, temperature=0.7)
    content = str(content).strip()
    if not content:
        raise RuntimeError("AI model returned an empty reply")
    return content


def _build_llm_messages(messages: List[Dict[str, str]], user_context: Dict[str, Any]) -> List[Dict[str, str]]:
    payload_messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    context_summary = _summarize_user_context(user_context)
    if context_summary:
        payload_messages.append(
            {
                "role": "system",
                "content": f"以下是当前用户背景信息，请在回答时适当参考：\n{context_summary}",
            }
        )

    payload_messages.extend(messages)
    return payload_messages


@health_manager_bp.route("/")
def index():
    return jsonify(
            {
                "service": "健康糖豆",
                "description": "健康管理智能体服务",
            "provider": ai_agent.settings.provider,
            "model": ai_agent.settings.chat_model,
            "endpoints": {
                "chat": "/api/chat",
                "legacy_chat": "/api/qwen/chat",
                "deepseek_chat": "/api/deepseek/chat",
            },
        }
    )


def _handle_chat_request():
    data = request.get_json(silent=True) or {}
    messages = _normalize_messages(data.get("messages") or [])
    user_context = data.get("user_context") or {}

    if not messages:
        return jsonify({"success": False, "error": "消息不能为空", "reply": ""}), 400

    try:
        llm_messages = _build_llm_messages(messages, user_context)
        reply = _call_deepseek(llm_messages)
        return jsonify(
            {
                "success": True,
                "provider": ai_agent.settings.provider,
                "model": ai_agent.settings.chat_model,
                "reply": reply,
                "thinking_process": [],
            }
        )
    except Exception as exc:  # noqa: BLE001
        latest_user_message = ""
        for message in reversed(messages):
            if message["role"] == "user":
                latest_user_message = message["content"]
                break

        logger.exception("健康糖豆调用 DeepSeek 失败: %s", exc)
        return jsonify(
            {
                "success": True,
                "provider": "fallback",
                "model": ai_agent.settings.chat_model,
                "reply": _fallback_reply(latest_user_message),
                "thinking_process": [],
                "error": str(exc),
            }
        )


@health_manager_bp.route("/api/chat", methods=["POST"])
@health_manager_bp.route("/api/deepseek/chat", methods=["POST"])
@health_manager_bp.route("/api/qwen/chat", methods=["POST"])
def chat():
    return _handle_chat_request()
