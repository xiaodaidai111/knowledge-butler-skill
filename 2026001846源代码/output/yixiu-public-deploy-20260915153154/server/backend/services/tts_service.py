"""
DashScope 语音合成 (TTS) 服务
使用通义语音合成 Sambert 模型将文本转换为语音。
"""

import io
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

try:
    import dashscope
    from dashscope.audio.tts import SpeechSynthesizer
except ImportError:
    dashscope = None
    SpeechSynthesizer = None

logger = logging.getLogger(__name__)

DEFAULT_TTS_MODEL = os.getenv("DASHSCOPE_TTS_MODEL", "sambert-zhichu-v1")


def _get_tts_api_key():
    return (
        os.getenv("DASHSCOPE_API_KEY_TUANTUAN")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("QWEN_API_KEY")
    )


def synthesize(text, voice=None, model=None, format_type="mp3", sample_rate=48000):
    """
    将文本转为语音音频。

    Args:
        text: 要合成的文本（最长 2000 字符）
        voice: 发音人，默认使用模型自带发音人
        model: TTS 模型名，默认 sambert-zhichu-v1
        format_type: 输出格式 mp3/wav/pcm
        sample_rate: 采样率

    Returns:
        bytes: 音频二进制数据

    Raises:
        RuntimeError: 依赖未安装或 API Key 未配置
        ValueError: 文本为空或过长
        Exception: 合成失败
    """
    if SpeechSynthesizer is None or dashscope is None:
        raise RuntimeError("服务器未安装 DashScope 语音合成依赖")

    api_key = _get_tts_api_key()
    if not api_key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY，无法启用语音合成")

    text = (text or "").strip()
    if not text:
        raise ValueError("文本内容不能为空")
    if len(text) > 2000:
        text = text[:2000]

    dashscope.api_key = api_key

    call_kwargs = {
        "model": model or DEFAULT_TTS_MODEL,
        "text": text,
        "format": format_type,
        "sample_rate": sample_rate,
    }
    if voice:
        call_kwargs["voice"] = voice

    result = SpeechSynthesizer.call(**call_kwargs)

    if result is None:
        raise Exception("语音合成无返回结果")

    status_code = getattr(result, "status_code", None)
    if status_code is not None and status_code != 200:
        msg = getattr(result, "message", "语音合成失败")
        raise Exception(f"语音合成失败({status_code}): {msg}")

    audio_data = getattr(result, "get_audio_data", None)
    if callable(audio_data):
        data = audio_data()
        if data:
            return data

    output = getattr(result, "output", None) or {}
    if isinstance(output, dict):
        audio = output.get("audio")
        if isinstance(audio, bytes):
            return audio
        if isinstance(audio, dict):
            url = audio.get("url") or audio.get("audio_url")
            if url:
                import requests
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                return resp.content

    raise Exception("语音合成返回数据解析失败")
