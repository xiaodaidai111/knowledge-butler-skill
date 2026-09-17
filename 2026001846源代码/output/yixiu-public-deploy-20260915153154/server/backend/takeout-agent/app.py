# -*- coding: utf-8 -*-
"""
慧识外卖 - 后端入口。
提供：健康知识库 RAG 对话、店铺卫生评分、外卖照片分析（视觉/启发式）。
API Key 仅通过环境变量或请求头传入，不在此文件中写死任何密钥。
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import re
from urllib.parse import urlparse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, make_response, render_template, request

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from PIL import Image
except Exception:
    Image = None

# 配置与数据层
from api_helpers import api_error, api_error_http, api_success
from config import (
    BASE_DIR,
    DATA_DIR,
    CHAT_HISTORY_LIMIT,
    MAX_CONTENT_LENGTH,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_CHAT_MODEL,
    DEEPSEEK_EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_CHAT_MODEL,
    OPENAI_VISION_MODEL,
    OPENAI_EMBEDDING_MODEL,
    RAG_TOP_K,
    SHOW_DEBUG_INFO,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
)
from database import (
    ensure_seed,
    get_knowledge_base_from_db,
    get_restaurants_from_db,
    load_json,
    save_json,
)

# 启动时确保数据库有数据（可从 JSON 导入）
ensure_seed()

# 知识库与样本店铺：优先从数据库读取，为空则从 JSON 回退
def _load_kb() -> List[Dict[str, Any]]:
    kb = get_knowledge_base_from_db()
    return kb if kb else load_json("knowledge_base.json", [])


def _load_sample_restaurants() -> List[Dict[str, Any]]:
    sample = get_restaurants_from_db()
    return sample if sample else load_json("sample_restaurants.json", [])


KB: List[Dict[str, Any]] = _load_kb()
SAMPLE: List[Dict[str, Any]] = _load_sample_restaurants()

# 知识库索引，供 RAG 检索与 embedding 使用
KB_INDEX: List[Tuple[str, Dict[str, Any]]] = []
for idx, entry in enumerate(KB):
    entry_id = str(entry.get("id") or f"kb_{idx}")
    KB_INDEX.append((entry_id, entry))
KB_LOOKUP = {entry_id: entry for entry_id, entry in KB_INDEX}

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.before_request
def handle_options_preflight() -> Optional[Any]:
    if request.method == "OPTIONS":
        return make_response("", 204)
    return None


@app.after_request
def add_cors_headers(response):
    allow = CORS_ALLOW_ORIGINS or "*"
    origin = request.headers.get("Origin")
    if allow == "*":
        response.headers["Access-Control-Allow-Origin"] = "*"
    else:
        allowed = [item.strip() for item in allow.split(",") if item.strip()]
        if origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = CORS_ALLOW_METHODS
    response.headers["Access-Control-Allow-Headers"] = CORS_ALLOW_HEADERS
    response.headers["Access-Control-Max-Age"] = "86400"
    return response


# ------------------------------ 页面与健康检查 ------------------------------

@app.route("/")
def index() -> str:
    """首页：简易测试前端，供本地验证；正式前端可替换或单独部署。"""
    return render_template("index.html")


@app.route("/simple")
def simple() -> str:
    """简易测试页：更轻量的接口联调页面。"""
    return render_template("simple.html")


@app.route("/api/health")
def health() -> Any:
    """健康检查，用于部署探活。统一格式：code=0, data 内为 status 与 time。"""
    return api_success({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"})


@app.route("/api/diagnose")
def diagnose() -> Any:
    """诊断 DeepSeek 接入配置，不返回敏感信息。"""
    api_key_header = request.headers.get("X-Api-Key", "").strip()
    base_url_header = request.headers.get("X-Base-Url", "").strip()
    effective_key = api_key_header or DEEPSEEK_API_KEY
    effective_base_url = base_url_header or DEEPSEEK_BASE_URL
    key_source = "header" if api_key_header else ("env" if DEEPSEEK_API_KEY else "missing")
    client = get_deepseek_client(api_key=effective_key, base_url=effective_base_url)
    reason = ""
    if OpenAI is None:
        reason = "missing_openai_dependency"
    elif not effective_key:
        reason = "missing_api_key"
    return api_success({
        "openai_dependency": OpenAI is not None,
        "client_ready": client is not None,
        "key_source": key_source,
        "api_key_preview": mask_api_key(effective_key) if effective_key else "",
        "base_url": safe_base_url(effective_base_url),
        "chat_model": DEEPSEEK_CHAT_MODEL,
        "embedding_model": DEEPSEEK_EMBEDDING_MODEL,
        "reason": reason,
    })


@app.route("/api/diagnose/ping", methods=["POST"])
def diagnose_ping() -> Any:
    """尝试调用大模型做最小化对话，返回错误原因，便于排查。"""
    api_key_header = request.headers.get("X-Api-Key", "").strip()
    base_url_header = request.headers.get("X-Base-Url", "").strip()
    effective_key = api_key_header or DEEPSEEK_API_KEY
    effective_base_url = base_url_header or DEEPSEEK_BASE_URL
    client = get_deepseek_client(api_key=effective_key, base_url=effective_base_url)
    if OpenAI is None:
        return api_error("OpenAI 依赖未安装", code=500, data={"reason": "missing_openai_dependency"})
    if not client:
        return api_error("API Key 缺失或无效", code=401, data={"reason": "missing_api_key"})
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_CHAT_MODEL,
            messages=[{"role": "user", "content": "ping"}],
        )
        text = (response.choices[0].message.content or "").strip()
        return api_success({"status": "ok", "reply": text or "pong", "mode": "chat.completions"})
    except Exception as chat_exc:
        reason = f"{type(chat_exc).__name__}: {chat_exc}"
        return api_error("模型调用失败", code=500, data={"reason": reason})


# ------------------------------ OpenAI 客户端 ------------------------------

def normalize_base_url(url: str) -> str:
    """将 Base URL 规范为带 /v1 后缀。"""
    url = (url or "").strip()
    if not url:
        return ""
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url = f"{url}/v1"
    return url


def get_deepseek_client(
    api_key: Optional[str] = None, base_url: Optional[str] = None
) -> Optional[OpenAI]:
    """根据 API Key 与 Base URL 构造 DeepSeek 客户端；无有效 Key 时返回 None。"""
    if OpenAI is None:
        return None
    resolved_key = (api_key or DEEPSEEK_API_KEY or "").strip()
    if not resolved_key:
        return None
    resolved_base = (base_url or DEEPSEEK_BASE_URL or "").strip()
    if resolved_base:
        return OpenAI(api_key=resolved_key, base_url=resolved_base)
    return OpenAI(api_key=resolved_key)

def get_request_client_with_reason() -> Tuple[Optional[OpenAI], str]:
    """
    从当前请求头或环境变量解析 DeepSeek 客户端。
    请求头：X-Api-Key、X-Base-Url。未传且环境变量无 API Key 时返回 (None, "missing_api_key")。
    """
    if OpenAI is None:
        return None, "missing_openai_dependency"
    api_key = request.headers.get("X-Api-Key", "").strip()
    base_url = request.headers.get("X-Base-Url", "").strip()
    env_key = DEEPSEEK_API_KEY
    if not api_key and not env_key:
        return None, "missing_api_key"
    if api_key:
        return get_deepseek_client(api_key=api_key, base_url=base_url), ""
    return get_deepseek_client(), ""


def mask_api_key(key: str) -> str:
    """只展示 API Key 的前后几位，避免泄露。"""
    key = (key or "").strip()
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def safe_base_url(url: str) -> str:
    """仅返回 scheme+host，避免暴露完整路径。"""
    url = (url or "").strip()
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return url.rstrip("/")


# ------------------------------ 店铺卫生评分 ------------------------------

def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def score_restaurant(restaurant: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据巡检分、评分、差评占比、投诉密度、包装风险等计算综合卫生分与等级。
    返回原字段 + hygiene_score, hygiene_grade, risk_tags, summary 等。
    """
    rating = float(restaurant.get("rating", 4.0))
    inspection = float(restaurant.get("last_inspection_score", 85))
    violations = int(restaurant.get("violations", 0))
    negative_reviews = int(restaurant.get("negative_reviews", 0))
    total_reviews = max(int(restaurant.get("total_reviews", 1)), 1)
    complaints = int(restaurant.get("complaint_count", 0))
    monthly_orders = max(int(restaurant.get("monthly_orders", 200)), 200)
    packaging_flags = restaurant.get("packaging_flags", [])

    packaging_risk = 0.0
    if "塑料高温" in packaging_flags:
        packaging_risk += 0.55
    if "密封不严" in packaging_flags:
        packaging_risk += 0.2
    if "二次加热" in packaging_flags:
        packaging_risk += 0.2
    if "餐具异味" in packaging_flags:
        packaging_risk += 0.15
    packaging_risk = min(packaging_risk, 1.0)

    negative_ratio = negative_reviews / total_reviews
    complaint_ratio = min(complaints / monthly_orders, 1.0)

    score = (
        inspection * 0.45
        + (rating / 5.0) * 100 * 0.25
        + (1 - negative_ratio) * 100 * 0.15
        + (1 - complaint_ratio) * 100 * 0.1
        + (1 - packaging_risk) * 100 * 0.05
    )
    score -= violations * 3
    score = clamp(score, 0, 100)

    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 55:
        grade = "C"
    else:
        grade = "D"

    risk_tags: List[str] = []
    if violations >= 3:
        risk_tags.append("历史违规偏多")
    if negative_ratio > 0.12:
        risk_tags.append("差评占比较高")
    if packaging_risk > 0.5:
        risk_tags.append("包装风险")
    if inspection < 80:
        risk_tags.append("卫生分偏低")
    if complaints > 6:
        risk_tags.append("投诉偏多")
    if not risk_tags:
        risk_tags.append("整体稳健")

    summary = (
        f"综合卫生分 {score:.1f}，评级 {grade}。"
        f"评分 {rating:.1f}，巡检 {inspection:.0f}，"
        f"差评占比 {negative_ratio * 100:.1f}%。"
    )

    scored = dict(restaurant)
    scored.update(
        {
            "hygiene_score": round(score, 1),
            "hygiene_grade": grade,
            "risk_tags": risk_tags,
            "packaging_risk": round(packaging_risk, 2),
            "negative_ratio": round(negative_ratio, 3),
            "complaint_ratio": round(complaint_ratio, 3),
            "summary": summary,
        }
    )
    return scored


def summarize_portfolio(restaurants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """对已评分的店铺列表做汇总：平均分、高风险数量、最低分店铺名。"""
    if not restaurants:
        return {
            "avg_score": 0,
            "high_risk_count": 0,
            "top_risk": "-",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
    avg_score = sum(r["hygiene_score"] for r in restaurants) / len(restaurants)
    high_risk = [r for r in restaurants if r["hygiene_score"] < 70]
    top_risk = min(restaurants, key=lambda item: item["hygiene_score"])
    return {
        "avg_score": round(avg_score, 1),
        "high_risk_count": len(high_risk),
        "top_risk": top_risk["name"],
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


# ------------------------------ 知识库与 RAG ------------------------------

def kb_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """基于关键词的简单检索（无 embedding 时的回退）。"""
    query = query.strip().lower()
    scored: List[Dict[str, Any]] = []
    for entry in KB:
        score = 0
        for keyword in entry.get("keywords", []):
            if keyword.lower() in query:
                score += 2
        if entry.get("title", "").lower() in query:
            score += 3
        scored.append({"score": score, "entry": entry})
    scored.sort(key=lambda item: item["score"], reverse=True)
    result = [item["entry"] for item in scored if item["score"] > 0]
    if not result:
        return []
    return result[:top_k]


def build_kb_text(entry: Dict[str, Any]) -> str:
    """将知识库条目转为用于 embedding 的纯文本。"""
    parts = [entry.get("title", "").strip()]
    keywords = entry.get("keywords", [])
    if keywords:
        parts.append("关键词: " + "、".join(keywords))
    content = entry.get("content", [])
    parts.extend(content)
    return "\n".join([part for part in parts if part])


def kb_signature() -> str:
    """知识库内容的哈希，用于判断 embedding 缓存是否失效。"""
    payload = json.dumps(KB, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ensure_kb_embeddings(client: OpenAI, embedding_model: str) -> Optional[Dict[str, Any]]:
    """若缓存有效则直接返回，否则调用 OpenAI 生成 embedding 并写入 data/kb_embeddings.json。"""
    signature = kb_signature()
    cache = load_json("kb_embeddings.json", {})
    if (
        cache.get("signature") == signature
        and cache.get("model") == embedding_model
        and cache.get("items")
    ):
        return cache
    if not KB_INDEX:
        return None
    texts = [build_kb_text(entry) for _, entry in KB_INDEX]
    try:
        response = client.embeddings.create(
            model=embedding_model,
            input=texts,
            encoding_format="float",
        )
    except Exception:
        return None
    items = []
    for (entry_id, _), data in zip(KB_INDEX, response.data):
        items.append({"id": entry_id, "embedding": data.embedding})
    cache = {
        "signature": signature,
        "model": embedding_model,
        "items": items,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    save_json("kb_embeddings.json", cache)
    return cache


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rag_search(
    client: OpenAI, query: str, top_k: int = 3, embedding_model: str = DEEPSEEK_EMBEDDING_MODEL
) -> List[Dict[str, Any]]:
    """RAG：对 query 做 embedding，与知识库向量比对，返回 top_k 条。"""
    cache = ensure_kb_embeddings(client, embedding_model)
    if not cache:
        return []
    try:
        response = client.embeddings.create(
            model=embedding_model,
            input=query,
            encoding_format="float",
        )
    except Exception:
        return []
    query_embedding = response.data[0].embedding
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for item in cache.get("items", []):
        entry = KB_LOOKUP.get(item.get("id"))
        if not entry:
            continue
        score = cosine_similarity(query_embedding, item.get("embedding", []))
        scored.append((score, entry))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored[:top_k]]


def resolve_context_entries(
    client: OpenAI,
    message: str,
    embedding_model: str,
    top_k: int,
) -> Tuple[List[Dict[str, Any]], str]:
    """优先使用向量检索，失败时回退到关键词检索。"""
    entries: List[Dict[str, Any]] = []
    mode = "rag"
    embedding_model = (embedding_model or "").strip()
    if embedding_model:
        entries = rag_search(client, message, top_k=top_k, embedding_model=embedding_model)
    if not entries:
        entries = kb_search(message, top_k=top_k)
        mode = "kb"
    return entries, mode


def normalize_history(
    history: List[Dict[str, Any]], limit: Optional[int] = None
) -> List[Dict[str, str]]:
    """只保留最近 limit 条 user/assistant 对话，且 content 非空；默认使用 CHAT_HISTORY_LIMIT 以保留足够上下文。"""
    limit = limit if limit is not None else CHAT_HISTORY_LIMIT
    normalized = []
    for item in history[-limit:]:
        role = str(item.get("role", "")).strip()
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            normalized.append({"role": role, "content": content})
    return normalized


def _find_restaurant_by_message(message: str) -> Optional[Dict[str, Any]]:
    """
    从用户消息中识别店铺名，在样本/数据库中查找并返回店铺数据。
    支持：「评估一下这家店：朝露烘焙工坊」「朝露烘焙工坊 怎么样」「评价 热辣档案馆」等。
    """
    message = (message or "").strip()
    if not message:
        return None
    # 常见引导词后的店名
    for prefix in ["评估一下这家店：", "评估这家店：", "评估：", "评价这家店：", "评价：", "这家店", "店铺"]:
        if prefix in message:
            name = message.split(prefix, 1)[-1].strip()
            name = name.rstrip("？?。，, ")
            if name:
                for r in SAMPLE:
                    if name in (r.get("name") or ""):
                        return r
                for r in SAMPLE:
                    if (r.get("name") or "").startswith(name) or name in (r.get("name") or ""):
                        return r
            break
    # 直接匹配：消息中是否包含某家店的全名
    for r in SAMPLE:
        store_name = (r.get("name") or "").strip()
        if store_name and store_name in message:
            return r
    # 短名或关键词：如「朝露」「烘焙工坊」
    for r in SAMPLE:
        store_name = (r.get("name") or "").strip()
        if len(store_name) >= 2 and any(store_name.find(part) >= 0 for part in message.split() if len(part) >= 2):
            for part in message.replace("：", " ").replace(":", " ").split():
                if len(part) >= 2 and part in store_name:
                    return r
    return None


def detect_analytics_intent(message: str) -> bool:
    """判断用户是否在询问店铺卫生/风险/评估等信息。"""
    if not message:
        return False
    keywords = [
        "卫生",
        "评估",
        "评分",
        "评价",
        "风险",
        "店铺",
        "门店",
        "这家店",
        "怎么样",
        "如何",
        "靠谱吗",
        "安全吗",
    ]
    if any(key in message for key in keywords):
        return True
    return _find_restaurant_by_message(message) is not None


def build_restaurant_reply(found: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    """基于店铺数据生成面向用户的回复。"""
    scored = score_restaurant(found)
    name = scored.get("name", "该店铺")
    score = scored.get("hygiene_score", 0)
    grade = scored.get("hygiene_grade", "")
    tags = scored.get("risk_tags", [])
    summary = scored.get("summary", "")
    if grade == "A" and score >= 90:
        head = f"我查了一下「{name}」，整体挺稳的。"
    elif grade in ("A", "B"):
        head = f"「{name}」我看过了，卫生这块还不错。"
    else:
        head = f"「{name}」的数据我看了下，有几项需要留意。"
    reply = (
        f"{head}\n\n"
        f"卫生分：{score}，等级：{grade}，风险点：{'、'.join(tags)}。\n"
        f"{summary}\n\n"
        "你还想看具体哪一项指标，或者需要我对比其他店铺吗？"
    )
    reply = sanitize_and_truncate_plain_text(reply, 200)
    return {
        "reply": reply,
        "sources": ["店铺数据"],
        "time": datetime.utcnow().isoformat() + "Z",
        "mode": "store",
        "error": reason,
        "restaurant": scored,
    }


def build_fallback_reply(
    message: str, history: List[Dict[str, str]], reason: str = ""
) -> Dict[str, Any]:
    """未使用大模型时的回复：能按店铺名查库并给出真实卫生评估，否则再走知识库 + 固定话术。"""
    candidates = kb_search(message)
    hints = [item.get("title", "") for item in candidates]
    lower_message = message.lower()
    is_greeting = any(word in lower_message for word in ["你好", "hello", "hi", "早上好", "晚上好"])
    ask_photo = any(word in message for word in ["照片", "图片", "识别", "上传", "拍照"])
    analytics_intent = detect_analytics_intent(message)

    # 优先：用户要评估具体店铺时，从数据里查并给出真实评分
    if analytics_intent or "评估" in message or "评价" in message or "怎么样" in message:
        found = _find_restaurant_by_message(message)
        if found:
            return build_restaurant_reply(found, reason=reason)
        if analytics_intent:
            intro = "这家店我这边暂时没有数据诶。你可以直接跟我说店名，比如「评估一下这家店：朝露烘焙工坊」，或者去【店铺画像】看看已经录入的几家。"
            knowledge_lines = []
            for entry in candidates:
                content = entry.get("content", [])
                if content:
                    knowledge_lines.append(f"• {entry.get('title', '')}：{content[0]}")
            if knowledge_lines:
                intro += "\n\n" + "\n".join(knowledge_lines)
            return {
                "reply": sanitize_and_truncate_plain_text(intro, 200),
                "sources": hints,
                "time": datetime.utcnow().isoformat() + "Z",
                "mode": "fallback",
                "error": reason,
            }

    if is_greeting:
        reply = "你好呀，我是慧识外卖小助手。可以帮你评估店铺卫生风险，或者分析外卖照片的包装与安全。你想先看哪家店？"
        return {
            "reply": sanitize_and_truncate_plain_text(reply, 200),
            "sources": [],
            "time": datetime.utcnow().isoformat() + "Z",
            "mode": "fallback",
            "error": reason,
        }
    elif ask_photo:
        intro = "想看图的话，直接上传一张外卖照片，我帮你看看包装材质和高温风险。"
        guidance = [
            "可以说说是热食还是冷食、要不要二次加热，或者有没有异味、渗漏啥的，我会一起考虑。",
        ]
    else:
        intro = "我根据知识库帮你整理了几条相关的，你看下。"
        guidance = []

    knowledge_lines = []
    for entry in candidates:
        content = entry.get("content", [])
        if content:
            knowledge_lines.append(f"{entry.get('title', '')}：{content[0]}")
    reply_parts = [intro]
    if knowledge_lines:
        reply_parts.append("\n".join(knowledge_lines))
    if guidance:
        reply_parts.append(guidance[0] if len(guidance) == 1 else "\n".join(guidance))
    reply = "\n\n".join(part for part in reply_parts if part)
    if SHOW_DEBUG_INFO and reason in ("missing_api_key", "missing_client"):
        reply += "\n\n（若已在项目里配置 .env 的 OPENAI_API_KEY 和 OPENAI_BASE_URL，记得保存后执行：pip install python-dotenv，再重启 python app.py）"
    reply = sanitize_and_truncate_plain_text(reply, 200)
    return {
        "reply": reply,
        "sources": hints,
        "time": datetime.utcnow().isoformat() + "Z",
        "mode": "fallback",
        "error": reason,
    }


def _build_session_context_block(context: Optional[Dict[str, Any]]) -> str:
    """根据前端传入的 context 拼出「当前会话上下文」说明，供 system prompt 使用，让智能体与用户正常连续交流。"""
    if not context:
        return ""
    lines = []
    last_image = context.get("last_image_analysis")
    if isinstance(last_image, dict):
        risk = last_image.get("risk_level") or last_image.get("risk_score")
        reply = last_image.get("reply") or ""
        warnings = last_image.get("warnings") or []
        lines.append(
            "【用户刚进行过外卖照片分析】"
            f" 风险等级/分数：{risk}；系统回复摘要：{reply[:200] if reply else '无'}；"
            f" 风险提示：{', '.join(warnings[:5]) if warnings else '无'}。"
        )
    last_restaurant = context.get("last_restaurant")
    if isinstance(last_restaurant, dict):
        name = last_restaurant.get("name") or "某店铺"
        score = last_restaurant.get("hygiene_score")
        grade = last_restaurant.get("hygiene_grade")
        tags = last_restaurant.get("risk_tags") or []
        lines.append(
            f"【用户刚查看过店铺卫生评分】 店铺：{name}；"
            f" 综合卫生分：{score}，等级：{grade}；风险标签：{', '.join(tags)}。"
        )
    if not lines:
        return ""
    return "\n\n当前会话上下文（可用于回答用户追问、澄清或延伸问题）：\n" + "\n".join(lines)


def sanitize_and_truncate_plain_text(text: Any, max_chars: int = 200) -> str:
    """
    Ensure agent reply is plain text (no markdown) and roughly limited length.
    """
    if text is None:
        return ""
    t = str(text)

    # Remove fenced code blocks.
    t = re.sub(r"```[\s\S]*?```", "", t)
    # Inline code: keep content.
    t = re.sub(r"`([^`]+)`", r"\1", t)
    # Bold/italic: keep content.
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    # Headings: remove leading '#'.
    t = re.sub(r"#{1,6}\s+", "", t)
    # Links: keep anchor text.
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    # Remove remaining common markdown symbols.
    t = re.sub(r"[*_`#~]", "", t)
    # Normalize excess blank lines.
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    if len(t) > max_chars:
        return t[: max(0, max_chars - 1)] + "…"
    return t


def build_chat_reply(
    message: str,
    history: List[Dict[str, str]],
    client: Optional[OpenAI] = None,
    chat_model: str = DEEPSEEK_CHAT_MODEL,
    embedding_model: str = DEEPSEEK_EMBEDDING_MODEL,
    context: Optional[Dict[str, Any]] = None,
    thinking_steps: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """RAG 对话：先检索知识库，再调用大模型生成回复；context 可带 last_image_analysis、last_restaurant 以增强上下文。"""
    client = client or get_deepseek_client()
    if not client:
        if thinking_steps is not None:
            thinking_steps.append({
                "type": "observation",
                "step": "LLM 不可用",
                "content": "missing_client"
            })
        return build_fallback_reply(message, history, reason="missing_client")
    context_entries, context_mode = resolve_context_entries(
        client, message, embedding_model=embedding_model, top_k=RAG_TOP_K
    )
    if thinking_steps is not None:
        thinking_steps.append({
            "type": "action",
            "step": "RAG 检索知识库",
            "content": f"top_k={RAG_TOP_K}"
        })
        thinking_steps.append({
            "type": "observation",
            "step": "RAG 检索完成",
            "content": f"命中={len(context_entries)} 条条目；mode={context_mode}"
        })

    context_blocks = []
    for entry in context_entries:
        title = entry.get("title", "")
        content = "\n".join(entry.get("content", []))
        context_blocks.append(f"[{title}]\n{content}")

    system_base = (
        "你是慧识外卖里的小助手，跟用户像朋友聊天一样聊外卖健康和卫生。\n"
        "语气：自然、亲切，偶尔可以用「嗯」「哈」「～」，别像念说明书，别用「根据」「综上所述」那种公文腔。\n"
        "内容：优先根据下面的「知识库」和「当前会话上下文」说；若知识库没有命中，可基于通用常识做简要答复，并明确不确定部分。\n"
        "如果用户在问刚上传的图、刚看过的店，就结合上下文里的分析结果回答，顺带给点实用建议。\n"
        "回复别太长：先一两句说清重点，再给几条好懂的建议，最后随口问一句或邀请他继续问。"
    )
    session_block = _build_session_context_block(context)
    if context_blocks:
        context_header = "\n\n知识库上下文：\n" + "\n\n".join(context_blocks)
    else:
        context_header = "\n\n知识库上下文：\n（暂无匹配条目）"
    system_prompt = system_base + context_header + (session_block if session_block else "")

    chat_messages = [{"role": "system", "content": system_prompt}]
    for item in normalize_history(history):
        chat_messages.append({"role": item["role"], "content": item["content"]})
    chat_messages.append({"role": "user", "content": message})

    try:
        if thinking_steps is not None:
            thinking_steps.append({
                "type": "action",
                "step": "调用对话模型生成回复",
                "content": f"model={chat_model}"
            })
        response = client.chat.completions.create(
            model=chat_model,
            messages=chat_messages,
        )
        reply_text = (response.choices[0].message.content or "").strip()
        if not reply_text:
            return build_fallback_reply(message, history, reason="empty_response")
        reply_text = sanitize_and_truncate_plain_text(reply_text, 200)
        if thinking_steps is not None:
            thinking_steps.append({
                "type": "observation",
                "step": "对话模型返回结果",
                "content": f"preview={reply_text[:120]}"
            })
        return {
            "reply": reply_text,
            "sources": [entry.get("title", "") for entry in context_entries],
            "time": datetime.utcnow().isoformat() + "Z",
            "mode": context_mode,
        }
    except Exception as chat_exc:
        reason = f"{type(chat_exc).__name__}: {chat_exc}"
        if thinking_steps is not None:
            thinking_steps.append({
                "type": "observation",
                "step": "对话生成失败",
                "content": reason[:200],
            })
        return build_fallback_reply(message, history, reason=reason)


# ------------------------------ 图片分析 ------------------------------

def _format_risk_explanation(
    risk_level: str, risk_score: float, warnings: List[str], mode: str = ""
) -> str:
    """生成面向用户的卫生/饮食安全风险说明文案。"""
    level_desc = {"高": "较高", "中": "中等", "低": "较低"}.get(risk_level, risk_level)
    head = f"综合风险等级为「{risk_level}」（分数 {risk_score:.0f}），整体饮食安全风险{level_desc}。"
    if warnings:
        head += " 主要关注点：" + "；".join(warnings) + "。"
    return head


def _format_safety_tips_heuristic(
    plastic_score: float,
    hot_food_score: float,
    oiliness_score: float,
    warnings: List[str],
) -> List[str]:
    """根据启发式分析结果生成具体安全建议。"""
    tips = []
    if plastic_score > 0.5:
        tips.append("建议确认包装材质耐热等级，热食尽量倒入陶瓷/玻璃器皿再加热。")
    if hot_food_score > 0.45:
        tips.append("高温食物注意烫口与密封性，避免长时间捂在塑料盒中。")
    if oiliness_score > 0.45:
        tips.append("油脂较多时建议搭配蔬菜或清淡汤品，注意膳食平衡。")
    if not tips:
        tips.append("当前未见明显高风险，仍建议注意包装完整与食用温度。")
    return tips


def analyze_image_heuristic(image_bytes: bytes, note: str = "") -> Dict[str, Any]:
    """不调用大模型时的启发式图片分析：亮度/色相/均匀度等简单特征。"""
    if Image is None:
        return {
            "status": "missing_dependency",
            "message": "Pillow 未安装，图片识别暂不可用。",
        }
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    sample = image.resize((120, 120))
    total = 0
    bright_count = 0
    warm_count = 0
    orange_count = 0
    greasy_count = 0
    sum_brightness = 0.0
    sum_brightness_sq = 0.0
    for r, g, b in sample.getdata():
        total += 1
        maxc = max(r, g, b)
        minc = min(r, g, b)
        brightness = (r + g + b) / 3
        saturation = maxc - minc
        sum_brightness += brightness
        sum_brightness_sq += brightness * brightness
        if brightness > 220:
            bright_count += 1
        if r > 170 and g > 100 and b < 90:
            warm_count += 1
        if r > 185 and g > 120 and b < 80:
            orange_count += 1
        if brightness > 160 and saturation > 60 and r > 170 and g > 110:
            greasy_count += 1
    if total == 0:
        return {"status": "error", "message": "无法解析图片"}
    bright_ratio = bright_count / total
    warm_ratio = warm_count / total
    orange_ratio = orange_count / total
    greasy_ratio = greasy_count / total
    mean_brightness = sum_brightness / total
    variance = max(sum_brightness_sq / total - mean_brightness**2, 0)
    std_brightness = math.sqrt(variance)
    uniformity = max(0.0, 1 - std_brightness / 90.0)
    plastic_score = 0.55 * uniformity + 0.45 * bright_ratio
    hot_food_score = 0.6 * warm_ratio + 0.4 * orange_ratio
    oiliness_score = 0.7 * greasy_ratio + 0.3 * warm_ratio
    risk_score = (0.4 * plastic_score + 0.35 * hot_food_score + 0.25 * oiliness_score) * 100
    risk_score = clamp(risk_score, 0, 100)
    if risk_score >= 70:
        level = "高"
    elif risk_score >= 45:
        level = "中"
    else:
        level = "低"
    warnings: List[str] = []
    if plastic_score > 0.55 and hot_food_score > 0.45:
        warnings.append("疑似塑料容器与热食接触风险")
    if oiliness_score > 0.45:
        warnings.append("油脂特征偏高，建议注意膳食平衡")
    if plastic_score > 0.6:
        warnings.append("包装材质可能偏塑料，建议确认耐热等级")
    if not warnings:
        warnings.append("未见明显高风险特征")
    # 为用户生成清晰的卫生与饮食安全说明，便于前端展示
    risk_explanation = _format_risk_explanation(level, risk_score, warnings, "heuristic")
    safety_tips = _format_safety_tips_heuristic(
        plastic_score, hot_food_score, oiliness_score, warnings
    )
    return {
        "status": "ok",
        "risk_score": round(risk_score, 1),
        "risk_level": level,
        "plastic_score": round(plastic_score, 3),
        "hot_food_score": round(hot_food_score, 3),
        "oiliness_score": round(oiliness_score, 3),
        "metrics": {
            "bright_ratio": round(bright_ratio, 3),
            "uniformity": round(uniformity, 3),
            "warm_ratio": round(warm_ratio, 3),
            "orange_ratio": round(orange_ratio, 3),
            "greasy_ratio": round(greasy_ratio, 3),
        },
        "warnings": warnings,
        "risk_explanation": risk_explanation,
        "safety_tips": safety_tips,
        "note": "该分析为启发式估计，仅供参考。",
        "mode": "heuristic",
    }


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """从模型返回文本中截取 JSON 对象。"""
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def analyze_image_with_openai(
    image_bytes: bytes,
    mime_type: str,
    note: str = "",
    client: Optional[OpenAI] = None,
    vision_model: str = OPENAI_VISION_MODEL,
) -> Optional[Dict[str, Any]]:
    """使用视觉大模型分析外卖图片，返回 risk_level、warnings、reply 等。"""
    client = client or get_openai_client()
    if not client:
        return None
    if not image_bytes:
        return {"status": "error", "message": "无法读取图片"}
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:{mime_type};base64,{base64_image}"
    prompt = (
        "你是外卖健康与饮食安全评估智能体。请根据图片判断外卖包装与食物风险，并严格返回以下 JSON（不要包含其他说明文字）：\n"
        "{\n"
        '  "risk_level": "高|中|低",\n'
        '  "risk_score": 0-100 的数字,\n'
        '  "plastic_score": 0-1,\n'
        '  "hot_food_score": 0-1,\n'
        '  "oiliness_score": 0-1,\n'
        '  "warnings": ["风险1", "风险2", ...],\n'
        '  "diet_risks": ["饮食风险点1", "饮食风险点2", ...],\n'
        '  "risk_explanation": "一段话：向用户说明本张外卖在卫生、包装安全、饮食安全方面的主要风险与关注点，语言清晰、易懂。",\n'
        '  "safety_tips": ["建议1", "建议2", ...],\n'
        '  "reply": "2-4 句对话式回复，总结风险并给出简要建议，结尾带一句追问（如：这是热食还是冷食？是否需要二次加热？）"\n'
        "}\n"
        "必须重点覆盖食品安全/饮食安全线索，包括但不限于：\n"
        "- 重油/高油脂（表面油光、油渍、油层明显）\n"
        "- 高温塑料接触（热食装在塑料盒/塑料袋、蒸汽或热气）\n"
        "- 渗漏/密封不良（汤汁外溢、盒盖不合、封口松散）\n"
        "- 生熟混放/交叉污染（生食与熟食同盒、共用酱料）\n"
        "- 颜色异常或疑似反复加热迹象\n"
        "要求：\n"
        "1) risk_explanation 必须明确涉及卫生、包装或饮食安全，且指出图中可见线索。\n"
        "2) diet_risks 至少 2 条，强调“饮食风险”而非包装描述。\n"
        "3) safety_tips 为 2-4 条可执行建议，尽量具体。\n"
        "4) 若无法从图中确定，可保守估计并说明不确定性。"
    )
    try:
        response = client.responses.create(
            model=vision_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt + (f"\n用户补充说明: {note}" if note.strip() else "")},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
        )
    except Exception:
        try:
            response = client.chat.completions.create(
                model=vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt + (f"\n用户补充说明: {note}" if note.strip() else "")},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
            )
            text = (response.choices[0].message.content or "").strip()
            data = extract_json_from_text(text)
            if not isinstance(data, dict):
                return None
            _ensure_vision_result_fields(data)
            return data
        except Exception:
            return None
    text = (response.output_text or "").strip()
    data = extract_json_from_text(text)
    if not isinstance(data, dict):
        return None
    _ensure_vision_result_fields(data)
    return data


def _ensure_vision_result_fields(data: Dict[str, Any]) -> None:
    """为视觉模型返回结果补全 risk_explanation、safety_tips、reply 等字段，便于前端统一展示。"""
    data.setdefault("status", "ok")
    data.setdefault("note", "图像模型评估结果，供参考。")
    data.setdefault("mode", "vision")
    warnings = data.get("warnings") or []
    risk_level = data.get("risk_level", "未知")
    risk_score = data.get("risk_score", 0)
    if not data.get("risk_explanation"):
        data["risk_explanation"] = _format_risk_explanation(
            str(risk_level), float(risk_score), warnings, "vision"
        )
    if not data.get("safety_tips"):
        data["safety_tips"] = [
            "建议确认包装耐热等级，热食尽量换用陶瓷/玻璃再加热。",
            "注意密封与食用温度，若有异味或渗漏请勿食用。",
        ]
    if not data.get("diet_risks"):
        data["diet_risks"] = data.get("warnings") or []
    if not data.get("reply") or not str(data.get("reply", "")).strip():
        data["reply"] = (
            "我已分析这张外卖照片。从卫生与饮食安全角度，"
            "建议重点关注包装材质与高温接触风险。你能告诉我这是热食还是冷食、是否需要二次加热吗？"
        )


def build_image_reply(result: Dict[str, Any], note: str = "") -> str:
    """将图片分析结果格式化为给用户看的回复：优先使用 risk_explanation 与 safety_tips，明确卫生与饮食安全说明。"""
    reply = result.get("reply") or ""
    if reply and str(reply).strip():
        return reply.strip()
    risk_explanation = result.get("risk_explanation") or ""
    safety_tips = result.get("safety_tips") or []
    diet_risks = result.get("diet_risks") or []
    risk_level = result.get("risk_level", "未知")
    risk_score = result.get("risk_score", "--")
    warnings = result.get("warnings", [])
    parts = []
    if risk_explanation:
        parts.append(risk_explanation)
    else:
        parts.append(f"我看到了照片，整体风险等级为 {risk_level}（分数 {risk_score}）。")
        if warnings:
            parts.append("主要关注点：" + "；".join(warnings))
    if safety_tips:
        parts.append("建议：" + "；".join(safety_tips))
    if diet_risks:
        parts.append("饮食风险提示：" + "；".join(diet_risks))
    if note.strip():
        parts.append(f"结合你的说明（{note.strip()}），请重点关注包装耐热与密封性。")
    parts.append("如果方便，请补充：这是热食还是冷食？是否需要二次加热？")
    reply = "\n".join(parts)
    return sanitize_and_truncate_plain_text(reply, 200)


# ------------------------------ API 路由（供前端对接） ------------------------------

@app.route("/api/demo/analyze")
def demo_analyze() -> Any:
    """演示用：对样本店铺做卫生评分并返回汇总与列表（按卫生分降序）。统一返回 code=0, data={ summary, restaurants }。"""
    scored = [score_restaurant(r) for r in SAMPLE]
    scored.sort(key=lambda item: item["hygiene_score"], reverse=True)
    return api_success({"summary": summarize_portfolio(scored), "restaurants": scored})


@app.route("/api/restaurant/score", methods=["POST"])
def api_score_restaurant() -> Any:
    """单店卫生评分：请求体为单条店铺 JSON，返回带 hygiene_score 等字段的对象。"""
    payload = request.get_json(silent=True) or {}
    scored = score_restaurant(payload)
    return api_success(scored)


def _chat_with_optional_image(
    message: str,
    history: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
    image_file=None,
) -> Dict[str, Any]:
    """
    统一对话逻辑：若无图则直接 RAG 对话；若有图则先识图，再把识图结果与用户文字合并成一条「用户消息」后走 RAG 对话，返回一条既有识图结论又像对话的回复。
    """
    client, reason = get_request_client_with_reason()
    image_analysis = None
    effective_message = message
    effective_context = dict(context) if context else {}
    found_restaurant = _find_restaurant_by_message(message) if message else None

    thinking_steps: List[Dict[str, Any]] = []

    def _finalize_react_out(out: Dict[str, Any]) -> Dict[str, Any]:
        reply_text = str(out.get("reply", "") or "")
        reflection_parts: List[str] = []

        # 反思：确保包含建议/追问；以及图/店铺模式下引用了分析结果
        if out.get("image_analysis") and isinstance(out["image_analysis"], dict):
            risk_level = out["image_analysis"].get("risk_level") or out["image_analysis"].get("risk_score")
            reflection_parts.append(f"已基于图片风险等级={risk_level}生成回复")
            if out["image_analysis"].get("safety_tips"):
                reflection_parts.append("安全建议已纳入输出")

        if out.get("restaurant") and isinstance(out["restaurant"], dict):
            reflection_parts.append("已基于店铺卫生评分生成回复")

        if reply_text:
            if any(k in reply_text for k in ["建议", "可以", "要不要", "建议：", "追问", "是否"]):
                reflection_parts.append("回复包含可执行建议/追问"
                                         )
            else:
                reflection_parts.append("回复未明显包含可执行建议/追问，已尽量补充风险与建议")
        else:
            reflection_parts.append("回复为空，已使用兜底文案")

        out["thinking_process"] = thinking_steps + [{
            "type": "reflection",
            "step": "结果反思与闭环校验",
            "content": "；".join(reflection_parts) if reflection_parts else "ok"
        }]
        return out

    thinking_steps.append({
        "type": "thought",
        "step": "接收用户请求",
        "content": f"message_preview={message[:80]}"
    })

    if found_restaurant:
        effective_context["last_restaurant"] = score_restaurant(found_restaurant)
        scored = effective_context["last_restaurant"]
        thinking_steps.append({
            "type": "action",
            "step": "店铺识别与评分准备",
            "content": f"name={scored.get('name','')}"
        })
        thinking_steps.append({
            "type": "observation",
            "step": "店铺卫生评分计算完成",
            "content": f"score={scored.get('hygiene_score')}, grade={scored.get('hygiene_grade')}"
        })
        if detect_analytics_intent(message):
            out = build_restaurant_reply(found_restaurant, reason=reason)
            return _finalize_react_out(out)

    if image_file and image_file.filename:
        image_bytes = image_file.read()
        mime_type = image_file.mimetype or "image/jpeg"
        note = message.strip() if message else ""
        result = None
        mode_hint = "vision" if client else "heuristic"
        thinking_steps.append({
            "type": "action",
            "step": "识别图片并提取风险要点",
            "content": f"mode_hint={mode_hint}"
        })
        if client:
            result = analyze_image_with_openai(
                image_bytes,
                mime_type,
                note=note,
                client=client,
                vision_model=(request.headers.get("X-Chat-Model") or DEEPSEEK_CHAT_MODEL).strip(),
            )
        if not result:
            result = analyze_image_heuristic(image_bytes, note=note)
            if reason:
                result["error"] = reason
        result["reply"] = build_image_reply(result, note)
        image_analysis = result
        effective_context["last_image_analysis"] = result
        thinking_steps.append({
            "type": "observation",
            "step": "图片风险分析完成",
            "content": f"risk_level={result.get('risk_level') or result.get('risk_score')}, mode={result.get('mode')}"
        })
        # 把识图结果转成一段「用户消息」里的上下文，让对话模型基于这段内容回复
        risk = result.get("risk_level") or result.get("risk_score")
        exp = result.get("risk_explanation") or ""
        tips = result.get("safety_tips") or []
        user_note = ("用户对此的说明或问题：" + message) if message else "用户希望根据这张图得到一些建议。"
        effective_message = (
            "【用户上传了一张外卖照片】分析结果：风险等级 %s。%s。建议：%s。%s"
            % (risk, exp, "；".join(tips[:3]), user_note)
        )

    if not effective_message.strip():
        out = build_fallback_reply(
            "请说一句话或上传一张图哦。",
            history,
            reason=reason or "missing_message",
        )
        return _finalize_react_out(out)

    if not client:
        if image_analysis:
            out = {
                "reply": image_analysis.get("reply") or build_image_reply(image_analysis, message),
                "sources": ["图片分析"],
                "time": datetime.utcnow().isoformat() + "Z",
                "mode": image_analysis.get("mode", "heuristic"),
                "error": reason,
                "image_analysis": image_analysis,
            }
            return _finalize_react_out(out)
        else:
            out = build_fallback_reply(effective_message, history, reason=reason)
        return _finalize_react_out(out)

    response = build_chat_reply(
        effective_message,
        history,
        client=client,
        chat_model=(request.headers.get("X-Chat-Model") or DEEPSEEK_CHAT_MODEL).strip(),
        embedding_model=(request.headers.get("X-Embedding-Model") or DEEPSEEK_EMBEDDING_MODEL).strip(),
        context=effective_context,
        thinking_steps=thinking_steps,
    )
    if image_analysis is not None:
        response["image_analysis"] = image_analysis
    return _finalize_react_out(response)


@app.route("/api/chat", methods=["POST"])
def api_chat() -> Any:
    """
    统一对话接口：既可纯文字，也可带图（文字+图一起发）。
    - JSON：{ "message", "history", "context" }。
    - 或 multipart/form-data：message、history（JSON 字符串）、image（文件）。
    有图时先识图，再结合用户文字用同一智能体回复，返回 { "reply", "sources", "time", "mode", "image_analysis"? }。
    """
    message = ""
    history = []
    context = None
    image_file = None

    if request.files.get("image") and request.files["image"].filename:
        # multipart：支持对话里带图
        message = (request.form.get("message") or "").strip()
        try:
            history = json.loads(request.form.get("history") or "[]")
        except Exception:
            history = []
        image_file = request.files["image"]
    else:
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        history = payload.get("history", [])
        context = payload.get("context")

    if not message and not image_file:
        return api_error("请输入文字或上传一张图片。", code=400)

    out = _chat_with_optional_image(message, history, context, image_file=image_file)
    return api_success(out)


@app.route("/api/image/analyze", methods=["POST"])
def api_image_analyze() -> Any:
    """
    照片分析：表单字段 image（文件）、note（可选文字）。
    返回含 risk_explanation（卫生/饮食安全说明）、safety_tips（建议）、reply（对话式回复）等，便于向用户指明风险。
    """
    if "image" not in request.files:
        return api_error_http("请上传图片", 400)
    image_file = request.files["image"]
    image_bytes = image_file.read()
    mime_type = image_file.mimetype or "image/jpeg"
    note = request.form.get("note", "").strip()
    client, reason = get_request_client_with_reason()
    result = None
    thinking_steps: List[Dict[str, Any]] = []
    thinking_steps.append({
        "type": "thought",
        "step": "接收图片分析请求",
        "content": f"note_preview={note[:40]}"
    })

    if client:
        thinking_steps.append({
            "type": "action",
            "step": "调用视觉大模型识别风险",
            "content": f"model_hint={request.headers.get('X-Chat-Model') or DEEPSEEK_CHAT_MODEL}"
        })
        result = analyze_image_with_openai(
            image_bytes,
            mime_type,
            note=note,
            client=client,
            vision_model=(request.headers.get("X-Chat-Model") or DEEPSEEK_CHAT_MODEL).strip(),
        )
    if result:
        thinking_steps.append({
            "type": "observation",
            "step": "视觉分析完成",
            "content": f"risk_level={result.get('risk_level') or result.get('risk_score')}"
        })
        if "reply" not in result or not str(result.get("reply", "")).strip():
            thinking_steps.append({
                "type": "action",
                "step": "生成对话式回复",
                "content": "build_image_reply"
            })
            result["reply"] = build_image_reply(result, note)
            thinking_steps.append({
                "type": "observation",
                "step": "回复生成完成",
                "content": f"preview={str(result.get('reply',''))[:120]}"
            })
        reflection = {"type": "reflection", "step": "结果反思与闭环校验", "content": "已完成图片风险 -> 对话回复 -> 建议闭环"}
        result["thinking_process"] = thinking_steps + [reflection]
        return api_success(result)

    thinking_steps.append({
        "type": "action",
        "step": "启用启发式图片分析",
        "content": "analyze_image_heuristic"
    })
    result = analyze_image_heuristic(image_bytes, note=note)
    result["reply"] = build_image_reply(result, note)
    thinking_steps.append({
        "type": "observation",
        "step": "启发式分析与回复生成完成",
        "content": f"risk_level={result.get('risk_level') or result.get('risk_score')}"
    })
    if reason:
        result["error"] = reason
    result["thinking_process"] = thinking_steps + [{
        "type": "reflection",
        "step": "结果反思与闭环校验",
        "content": "已完成图片风险 -> 对话回复 -> 建议闭环（启发式）"
    }]
    return api_success(result)

if __name__ == "__main__":
    # 启动时提示是否已加载 .env 配置，方便排查
    key_status = "已配置" if DEEPSEEK_API_KEY else "未配置（将使用离线/fallback 模式）"
    base_status = DEEPSEEK_BASE_URL or "未设置（直连官方）"
    print("[慧识外卖] DEEPSEEK_API_KEY: %s | DEEPSEEK_BASE_URL: %s" % (key_status, base_status))
    app.run(host="0.0.0.0", port=5001, debug=True)
