import ipaddress
import logging
import os
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

try:
    import dashscope
    from dashscope.audio.asr import Transcription
except ImportError:  # pragma: no cover - runtime dependency check
    dashscope = None
    Transcription = None


speech_asr_bp = Blueprint("speech_asr", __name__)
logger = logging.getLogger(__name__)

DEFAULT_ASR_MODEL = os.getenv("DASHSCOPE_ASR_MODEL", "paraformer-v2")
DEFAULT_DASHSCOPE_API_URL = os.getenv(
    "DASHSCOPE_BASE_HTTP_API_URL", "https://dashscope.aliyuncs.com/api/v1"
)
ALLOWED_AUDIO_EXTENSIONS = {
    "aac",
    "amr",
    "avi",
    "flac",
    "flv",
    "m4a",
    "mkv",
    "mov",
    "mp3",
    "mp4",
    "mpeg",
    "ogg",
    "opus",
    "wav",
    "webm",
    "wma",
    "wmv",
}


def _json_response(code, message, data=None):
    return jsonify({"code": code, "message": message, "data": data}), code


def _object_get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _get_asr_api_key():
    return (
        os.getenv("DASHSCOPE_API_KEY_TUANTUAN")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("QWEN_API_KEY")
    )


def _get_audio_upload_dir():
    base_dir = Path(current_app.root_path) / current_app.config.get("UPLOAD_FOLDER", "uploads")
    audio_dir = base_dir / "voice_asr"
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir


def _is_allowed_audio(filename):
    suffix = Path(filename).suffix.lower().lstrip(".")
    return bool(suffix) and suffix in ALLOWED_AUDIO_EXTENSIONS


def _looks_private_host(hostname):
    if not hostname:
        return True

    if hostname in {"localhost", "127.0.0.1"}:
        return True

    try:
        ip_value = ipaddress.ip_address(hostname)
    except ValueError:
        return False

    return (
        ip_value.is_private
        or ip_value.is_loopback
        or ip_value.is_link_local
        or ip_value.is_reserved
    )


def _build_public_base_url():
    configured_url = _get_configured_public_base_url()
    if configured_url:
        return configured_url.rstrip("/")

    inferred_url = _infer_public_request_url()
    parsed = urlparse(inferred_url)
    if _looks_private_host(parsed.hostname):
        return None
    return inferred_url


def _infer_public_request_url():
    forwarded_host = request.headers.get("X-Forwarded-Host", "").split(",")[0].strip()
    if forwarded_host:
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "http").split(",")[0].strip()
        return f"{forwarded_proto}://{forwarded_host}".rstrip("/")

    return request.url_root.rstrip("/")


def _get_configured_public_base_url():
    return (
        os.getenv("ASR_PUBLIC_BASE_URL")
        or os.getenv("PUBLIC_BASE_URL")
        or os.getenv("TUANTUAN_PUBLIC_BASE_URL")
    )


def _download_transcription_json(transcription_url):
    response = requests.get(transcription_url, timeout=30)
    response.raise_for_status()
    return response.json()


def _extract_transcription_text(transcription_payload):
    transcripts = transcription_payload.get("transcripts") or []
    transcript_texts = []
    sentences = []

    for transcript in transcripts:
        transcript_text = (transcript.get("text") or "").strip()
        if transcript_text:
            transcript_texts.append(transcript_text)

        for sentence in transcript.get("sentences") or []:
            sentence_text = (sentence.get("text") or "").strip()
            if not sentence_text:
                continue

            sentences.append(
                {
                    "text": sentence_text,
                    "begin_time": sentence.get("begin_time"),
                    "end_time": sentence.get("end_time"),
                    "sentence_id": sentence.get("sentence_id"),
                    "speaker_id": sentence.get("speaker_id"),
                }
            )

    text = "\n".join(transcript_texts).strip()
    if not text and sentences:
        text = "\n".join(sentence["text"] for sentence in sentences).strip()

    return text, sentences


def _format_subtask_failure_message(first_result):
    code = _object_get(first_result, "code")
    message = _object_get(first_result, "message", "语音识别失败")
    detail = "，".join(str(item) for item in (code, message) if item)
    lowered_detail = detail.lower()

    if "no_valid" in lowered_detail or "no valid" in lowered_detail or "downloadfailed" in lowered_detail:
        return (
            "DashScope 没有拿到有效音频文件。请检查 ASR_PUBLIC_BASE_URL 是否是公网可访问的后端地址，"
            "并确认录音格式为 mp3/wav/m4a。"
            f"原始错误：{detail}"
        )

    return message


@speech_asr_bp.route("/api/speech/uploads/<path:filename>", methods=["GET"])
def serve_uploaded_audio(filename):
    upload_dir = _get_audio_upload_dir()
    return send_from_directory(str(upload_dir), filename, as_attachment=False, max_age=300)


@speech_asr_bp.route("/api/speech/health", methods=["GET"])
def speech_health():
    configured_public_base_url = _get_configured_public_base_url()
    inferred_public_base_url = None
    if request:
        inferred_url = _infer_public_request_url()
        parsed = urlparse(inferred_url)
        if not _looks_private_host(parsed.hostname):
            inferred_public_base_url = inferred_url

    public_base_url_ready = bool(configured_public_base_url or inferred_public_base_url)
    return _json_response(
        200,
        "语音识别服务已连接",
        {
            "dashscope_dependency": Transcription is not None and dashscope is not None,
            "api_key_configured": bool(_get_asr_api_key()),
            "public_base_url_configured": bool(configured_public_base_url),
            "public_base_url_ready": public_base_url_ready,
            "model": DEFAULT_ASR_MODEL,
        },
    )


@speech_asr_bp.route("/api/speech/transcribe", methods=["POST"])
def transcribe_audio():
    if Transcription is None or dashscope is None:
        return _json_response(500, "服务器未安装 DashScope 语音识别依赖")

    api_key = _get_asr_api_key()
    if not api_key:
        return _json_response(500, "未配置 DASHSCOPE_API_KEY，无法启用语音输入")

    uploaded_audio = request.files.get("audio") or request.files.get("file")
    if not uploaded_audio or not uploaded_audio.filename:
        return _json_response(400, "请上传音频文件")

    if not _is_allowed_audio(uploaded_audio.filename):
        supported = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        return _json_response(400, f"暂不支持该音频格式，请使用以下格式之一：{supported}")

    public_base_url = _build_public_base_url()
    if not public_base_url:
        return _json_response(
            400,
            "当前后端地址不是公网可访问地址，请先配置 ASR_PUBLIC_BASE_URL 再使用语音输入",
        )

    original_name = secure_filename(uploaded_audio.filename)
    suffix = Path(original_name).suffix.lower() or ".mp3"
    saved_name = f"{uuid.uuid4().hex}{suffix}"
    upload_dir = _get_audio_upload_dir()
    saved_path = upload_dir / saved_name
    uploaded_audio.save(saved_path)

    audio_url = f"{public_base_url}/api/speech/uploads/{saved_name}"
    model_name = (request.form.get("model") or DEFAULT_ASR_MODEL).strip() or DEFAULT_ASR_MODEL

    try:
        dashscope.api_key = api_key
        dashscope.base_http_api_url = DEFAULT_DASHSCOPE_API_URL

        transcription_options = {}
        if model_name == "paraformer-v2":
            transcription_options["language_hints"] = ["zh", "en"]

        task_response = Transcription.async_call(
            model=model_name,
            file_urls=[audio_url],
            **transcription_options,
        )
        task_or_id = _object_get(_object_get(task_response, "output", {}), "task_id") or task_response
        transcribe_response = Transcription.wait(task=task_or_id)

        if _object_get(transcribe_response, "status_code") != 200:
            return _json_response(
                502,
                _object_get(transcribe_response, "message", "DashScope 语音识别调用失败"),
            )

        output = _object_get(transcribe_response, "output", {}) or {}
        task_id = _object_get(output, "task_id")
        results = _object_get(output, "results", []) or []
        if not results:
            return _json_response(502, "语音识别任务未返回结果", {"task_id": task_id})

        first_result = results[0]
        if _object_get(first_result, "subtask_status") != "SUCCEEDED":
            return _json_response(
                502,
                _format_subtask_failure_message(first_result),
                {
                    "task_id": task_id,
                    "code": _object_get(first_result, "code"),
                },
            )

        transcription_url = _object_get(first_result, "transcription_url")
        if not transcription_url:
            return _json_response(502, "语音识别成功，但未返回可下载的转写结果")

        transcription_payload = _download_transcription_json(transcription_url)
        transcribed_text, sentences = _extract_transcription_text(transcription_payload)
        if not transcribed_text:
            return _json_response(502, "语音识别结果为空", {"task_id": task_id})

        return _json_response(
            200,
            "语音识别成功",
            {
                "text": transcribed_text,
                "sentences": sentences,
                "task_id": task_id,
                "model": model_name,
            },
        )
    except requests.RequestException as exc:
        logger.exception("下载 DashScope 转写结果失败")
        return _json_response(502, f"下载语音识别结果失败：{exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("语音识别失败")
        return _json_response(500, f"语音识别失败：{exc}")
    finally:
        try:
            if saved_path.exists():
                saved_path.unlink()
        except OSError:
            logger.warning("临时音频文件删除失败: %s", saved_path)
