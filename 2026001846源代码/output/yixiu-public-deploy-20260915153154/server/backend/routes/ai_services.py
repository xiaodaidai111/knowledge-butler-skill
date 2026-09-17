import json
import logging

from flask import Blueprint, request

from services.ai_gateway import ai_agent
from utils import error_response, success_response, validate_required_fields

ai_services_bp = Blueprint("ai_services", __name__)
logger = logging.getLogger(__name__)


def _json_or_text(text):
    parsed = ai_agent.parse_json(text)
    return parsed if parsed else {"analysis": text}


@ai_services_bp.route("/api/ai/status", methods=["GET"])
def ai_status():
    """返回统一 AI 网关状态，不暴露密钥。"""
    return success_response(ai_agent.status(), "AI配置读取成功")


@ai_services_bp.route("/api/ai/image-generation", methods=["POST"])
def generate_image():
    """文生图 API。"""
    try:
        data = request.get_json(silent=True) or {}
        is_valid, error_msg = validate_required_fields(data, ["prompt"])
        if not is_valid:
            return error_response(400, error_msg)

        prompt = str(data.get("prompt", "")).strip()
        if len(prompt) > 500:
            return error_response(400, "提示词不能超过500字")

        urls = ai_agent.generate_image(prompt)
        if not urls:
            return error_response(500, "图片生成失败：未返回图片URL")
        return success_response({"image_url": urls[0], "image_urls": urls, "prompt": prompt}, "图片生成成功")
    except Exception as exc:
        logger.exception("图片生成失败: %s", exc)
        return error_response(500, f"图片生成API调用失败:{str(exc)}")


@ai_services_bp.route("/api/ai/image-analysis", methods=["POST"])
def analyze_image():
    """图片理解 API。"""
    try:
        data = request.get_json(silent=True) or {}
        image_url = str(data.get("image_url", "")).strip()
        image_base64 = str(data.get("image_base64", "")).strip()
        prompt = str(data.get("prompt") or "请评价这张图片，并给出识别结果、风险点、评分和建议。").strip()

        if not image_url and not image_base64:
            return error_response(400, "请提供图片URL或base64编码")

        system_prompt = (
            "你是专业的检修图片分析助手。请识别设备、部件、故障现象、风险点和处理建议。"
            "尽量返回 JSON，字段包含 findings, equipment, fault_signs, risk_points, analysis, score, suggestion, exp_reward。"
            "必须按设备检修场景解释，不要输出餐饮或健康评估语义。"
        )
        response_text = ai_agent.vision(
            prompt=prompt,
            image_url=image_url or None,
            image_base64=image_base64 or None,
            system_prompt=system_prompt,
            json_mode=False,
        )
        result = _json_or_text(response_text)
        findings = result.get("findings") or result.get("fault_signs") or result.get("ingredients", [])
        return success_response(
            {
                "findings": findings,
                "equipment": result.get("equipment", ""),
                "fault_signs": result.get("fault_signs", findings),
                "risk_points": result.get("risk_points", []),
                "ingredients": findings,
                "analysis": result.get("analysis", response_text),
                "score": result.get("score", 5.0),
                "suggestion": result.get("suggestion", ""),
                "exp_reward": result.get("exp_reward", 10),
                "raw": response_text,
                "provider": ai_agent.settings.provider,
                "model": ai_agent.settings.vision_model,
            },
            "图片分析成功",
        )
    except Exception as exc:
        logger.exception("图片分析失败: %s", exc)
        return error_response(500, f"图片分析API调用失败:{str(exc)}")


@ai_services_bp.route("/api/ai/chat-with-image", methods=["POST"])
def chat_with_image():
    """图文对话 API。"""
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()
        image_url = str(data.get("image_url", "")).strip()
        image_base64 = str(data.get("image_base64", "")).strip()
        conversation_id = str(data.get("conversation_id", "")).strip()

        if not message and not image_url and not image_base64:
            return error_response(400, "请提供消息或图片")

        response_text = ai_agent.vision(
            prompt=message or "请分析这张图片。",
            image_url=image_url or None,
            image_base64=image_base64 or None,
            system_prompt=(
                "你是智学问修助手，擅长设备检修、故障诊断和知识库问答。"
                "用户给出图片时，请结合图像和文字给出可执行建议。"
            ),
        )

        return success_response(
            {
                "response": response_text,
                "conversation_id": conversation_id,
                "provider": ai_agent.settings.provider,
                "model": ai_agent.settings.vision_model,
            },
            "对话成功",
        )
    except Exception as exc:
        logger.exception("图文对话失败: %s", exc)
        return error_response(500, f"对话API调用失败:{str(exc)}")

