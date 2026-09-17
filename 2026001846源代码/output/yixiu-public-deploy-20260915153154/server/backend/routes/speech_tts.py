"""
语音合成 (TTS) API 路由
提供文本转语音的 HTTP 接口。
"""

import logging

from flask import Blueprint, jsonify, request, Response

speech_tts_bp = Blueprint("speech_tts", __name__)
logger = logging.getLogger(__name__)


def _json_response(code, message, data=None):
    return jsonify({"code": code, "message": message, "data": data}), code


@speech_tts_bp.route("/api/speech/tts/health", methods=["GET"])
def tts_health():
    from services.tts_service import _get_tts_api_key, DEFAULT_TTS_MODEL

    try:
        from dashscope.audio.tts import SpeechSynthesizer  # noqa: F401
        dep_ok = True
    except ImportError:
        dep_ok = False

    return _json_response(200, "语音合成服务状态", {
        "dashscope_dependency": dep_ok,
        "api_key_configured": bool(_get_tts_api_key()),
        "model": DEFAULT_TTS_MODEL,
    })


@speech_tts_bp.route("/api/speech/tts", methods=["POST"])
def text_to_speech():
    """
    接收文本，返回合成的语音音频。

    请求体 (JSON):
        text: 要合成的文本（必填，最长 2000 字符）
        voice: 发音人（可选，如 zhichu、zhimi、zhixiaobai）
        model: TTS 模型（可选）
        format: 输出格式（可选，默认 mp3）

    返回:
        成功: 音频二进制流 (Content-Type: audio/mpeg)
        失败: JSON 错误信息
    """
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return _json_response(400, "请提供要合成的文本")

    if len(text) > 2000:
        text = text[:2000]

    voice = data.get("voice") or None
    model = data.get("model") or None
    format_type = data.get("format") or "mp3"

    try:
        from services.tts_service import synthesize
        audio_bytes = synthesize(
            text=text,
            voice=voice,
            model=model,
            format_type=format_type,
        )

        content_type = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "pcm": "audio/pcm",
        }.get(format_type, "audio/mpeg")

        return Response(
            audio_bytes,
            mimetype=content_type,
            headers={
                "Content-Disposition": f"inline; filename=tts_output.{format_type}",
                "Cache-Control": "no-cache",
            },
        )
    except ValueError as exc:
        return _json_response(400, str(exc))
    except RuntimeError as exc:
        return _json_response(500, str(exc))
    except Exception as exc:
        logger.exception("语音合成失败")
        return _json_response(502, f"语音合成失败: {exc}")
