"""Curated, cache-backed public AI updates for the Yixiu workbench.

The browser never talks to third-party feeds directly.  This service only reads
an allow-listed set of primary sources, keeps a 72 hour local cache, converts
available cover images to local WebP files, and falls back to the bundled
editorial selection when the public network is unavailable.
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
CACHE_PATH = DATA_DIR / "public_ai_updates.json"
IMAGE_DIR = DATA_DIR / "public_ai_update_images"
REFRESH_HOURS = max(24, min(168, int(os.getenv("PUBLIC_AI_UPDATE_HOURS", "72"))))
REQUEST_TIMEOUT = (4, 12)
MAX_FEED_BYTES = 2_500_000
MAX_IMAGE_BYTES = 8_000_000

_CACHE_LOCK = threading.Lock()

FEEDS = (
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "fallback": "/static/yixiu-carousel-gemini-live.webp"},
    {"name": "GitHub Blog", "url": "https://github.blog/ai-and-ml/feed/", "fallback": "/static/yixiu-carousel-vidu-s2.webp"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "fallback": "/static/yixiu-carousel-intern-s2.webp"},
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml", "fallback": "/static/yixiu-carousel-gemini-live.webp"},
)

CURATED_REPOSITORIES = (
    "langgenius/dify",
    "getzep/graphiti",
    "HKUDS/nanobot",
    "langchain-ai/langgraph",
    "langchain-ai/deepagents",
)

ALLOWED_IMAGE_HOST_SUFFIXES = (
    "blog.google",
    "googleusercontent.com",
    "gstatic.com",
    "github.blog",
    "githubusercontent.com",
    "openai.com",
    "oaistatic.com",
    "images.ctfassets.net",
    "huggingface.co",
    "hf.co",
)

DEFAULT_ITEMS = [
    {
        "id": "curated-vidu-s2",
        "title": "Vidu S2 技术解析：实时编辑、实时交互、探索空间视频",
        "summary": "生数科技发布 Vidu S2-Avatar 与 Vidu S2-Editing 双模型，支持实时数字人、实时视频编辑与空间视频传输。",
        "source": "生数科技",
        "date": "2026-09-15",
        "link": "https://mp.weixin.qq.com/s/f2uewxWhxWlq_JOQqFvmiw",
        "image": "/static/yixiu-carousel-vidu-s2.webp",
    },
    {
        "id": "curated-intern-s2",
        "title": "最懂科学的开源基础大模型「书生-S2」发布",
        "summary": "上海人工智能实验室发布书生-S2，以科学推理、通用能力和按需激活的 Memory 机制服务复杂研发任务。",
        "source": "书生 Intern",
        "date": "2026-09-14",
        "link": "https://mp.weixin.qq.com/s/EZghVJB13rJTRfBv2_U0Xw",
        "image": "/static/yixiu-carousel-intern-s2.webp",
    },
    {
        "id": "curated-huawei-360",
        "title": "360 与昇腾 AI 联合打造解决方案，为 AI Agent 全面提速",
        "summary": "在华为全联接大会 2026 上，360 与昇腾 AI 联合打造面向 AI Agent 的解决方案，围绕 Agent 的构建与运行效率做联合优化。",
        "source": "MSN 科技",
        "date": "2026-09-19",
        "link": "https://www.msn.cn/zh-cn/%E6%8A%80%E6%9C%AF/%E6%8A%80%E6%9C%AF%E5%85%AC%E5%8F%B8/%E5%8D%8E%E4%B8%BA%E5%85%A8%E8%81%94%E6%8E%A5%E5%A4%A7%E4%BC%9A2026-360%E4%B8%8E%E6%98%87%E8%85%BEai%E8%81%94%E5%90%88%E6%89%93%E9%80%A0%E8%A7%A3%E5%86%B3%E6%96%B9%E6%A1%88-%E4%B8%BAai-agent%E5%85%A8%E9%9D%A2%E6%8F%90%E9%80%9F/ar-AA2cxJKG",
        "image": "/static/yixiu-carousel-huawei-360.webp",
    },
]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _text(node: ElementTree.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in list(node):
        if _local_name(child.tag) in wanted and child.text:
            return child.text.strip()
    return ""


def _clean_markup(value: str, limit: int = 220) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value or "", flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", html.unescape(value)).strip()
    if len(value) > limit:
        value = value[: limit - 1].rstrip("，,。.!！?？ ") + "…"
    return value


def _published(value: str) -> tuple[str, float]:
    raw = (value or "").strip()
    parsed: datetime | None = None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            parsed = None
    if parsed is None:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%d"), parsed.timestamp()


def _safe_https_url(value: str) -> str:
    value = html.unescape((value or "").strip())
    parsed = urlparse(value)
    return value if parsed.scheme == "https" and parsed.netloc else ""


def _extract_image(node: ElementTree.Element, description: str) -> str:
    for child in list(node):
        local = _local_name(child.tag)
        candidate = child.attrib.get("url", "") if local in {"content", "thumbnail", "enclosure"} else ""
        if candidate and ("image" in child.attrib.get("type", "") or local != "enclosure"):
            return _safe_https_url(candidate)
    match = re.search(r"<img[^>]+src=[\"']([^\"']+)", description or "", flags=re.I)
    return _safe_https_url(match.group(1)) if match else ""


def _fetch_feed(feed: dict[str, str]) -> list[dict[str, Any]]:
    response = requests.get(
        feed["url"],
        headers={"User-Agent": "Yixiu-Workbench/1.0 (+public AI update cache)"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    if len(response.content) > MAX_FEED_BYTES:
        raise ValueError("feed response is too large")
    root = ElementTree.fromstring(response.content)
    nodes = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    results: list[dict[str, Any]] = []
    for node in nodes[:12]:
        title = _clean_markup(_text(node, "title"), 120)
        link = _safe_https_url(_text(node, "link", "guid"))
        if not link:
            for child in list(node):
                if _local_name(child.tag) == "link":
                    link = _safe_https_url(child.attrib.get("href", ""))
                    if link:
                        break
        description = _text(node, "description", "summary", "content", "encoded")
        date, timestamp = _published(_text(node, "pubdate", "published", "updated", "date"))
        if not title or not link:
            continue
        digest = hashlib.sha1(link.encode("utf-8")).hexdigest()[:16]
        results.append(
            {
                "id": f"update-{digest}",
                "title": title,
                "summary": _clean_markup(description) or "来自官方发布页的最新 AI 与软件工程动态。",
                "source": feed["name"],
                "date": date,
                "timestamp": timestamp,
                "link": link,
                "remote_image": _extract_image(node, description),
                "fallback": feed["fallback"],
            }
        )
    return results


def _allowed_image_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_IMAGE_HOST_SUFFIXES)


def _cache_image(url: str, item_id: str) -> str:
    if not url or not _allowed_image_url(url):
        return ""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    target = IMAGE_DIR / f"{item_id}.webp"
    if target.exists() and target.stat().st_size > 256:
        return f"/api/yixiu/content/updates/{item_id}/image"
    response = requests.get(url, headers={"User-Agent": "Yixiu-Workbench/1.0"}, timeout=REQUEST_TIMEOUT, stream=True)
    response.raise_for_status()
    final_url = response.url or url
    if not _allowed_image_url(final_url):
        raise ValueError("image redirect left the allow-list")
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_IMAGE_BYTES:
            raise ValueError("image response is too large")
        chunks.append(chunk)
    raw = b"".join(chunks)
    if not raw:
        return ""
    try:
        import cv2
        import numpy as np

        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            return ""
        height, width = image.shape[:2]
        if width < 360 or height < 180:
            return ""
        if width > 1600:
            scale = 1600 / width
            image = cv2.resize(image, (1600, max(1, int(height * scale))), interpolation=cv2.INTER_AREA)
        ok, encoded = cv2.imencode(".webp", image, [int(cv2.IMWRITE_WEBP_QUALITY), 86])
        if not ok:
            return ""
        temporary = target.with_suffix(".tmp.webp")
        temporary.write_bytes(encoded.tobytes())
        temporary.replace(target)
        return f"/api/yixiu/content/updates/{item_id}/image"
    except Exception as exc:  # noqa: BLE001
        logger.info("public update cover could not be cached as WebP: %s", exc)
        return ""


def _fetch_repository(repository: str) -> dict[str, Any]:
    response = requests.get(
        f"https://api.github.com/repos/{repository}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Yixiu-Workbench/1.0"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "repo": data.get("html_url") or f"https://github.com/{repository}",
        "full_name": data.get("full_name") or repository,
        "stars": int(data.get("stargazers_count") or 0),
        "description": _clean_markup(str(data.get("description") or ""), 180),
        "language": data.get("language") or "",
        "updated_at": str(data.get("updated_at") or "")[:10],
        "homepage": _safe_https_url(str(data.get("homepage") or "")),
    }


def _read_cache() -> dict[str, Any] | None:
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and isinstance(data.get("items"), list) else None
    except (OSError, ValueError, TypeError):
        return None


def _cache_is_fresh(cache: dict[str, Any]) -> bool:
    try:
        refreshed = datetime.fromisoformat(str(cache.get("refreshed_at", "")))
        if refreshed.tzinfo is None:
            refreshed = refreshed.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - refreshed.astimezone(timezone.utc) < timedelta(hours=REFRESH_HOURS)
    except (TypeError, ValueError):
        return False


def _write_cache(payload: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = CACHE_PATH.with_suffix(".tmp.json")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(CACHE_PATH)


def _refresh() -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    projects: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=6, thread_name_prefix="yixiu-updates") as executor:
        feed_jobs = {executor.submit(_fetch_feed, feed): feed for feed in FEEDS}
        repo_jobs = {executor.submit(_fetch_repository, repo): repo for repo in CURATED_REPOSITORIES}
        for future in as_completed([*feed_jobs, *repo_jobs]):
            try:
                result = future.result()
                if isinstance(result, list):
                    candidates.extend(result)
                elif isinstance(result, dict):
                    projects.append(result)
            except Exception as exc:  # noqa: BLE001
                label = feed_jobs.get(future, repo_jobs.get(future, "source"))
                logger.info("public update source unavailable (%s): %s", label, exc)

    candidates.sort(key=lambda item: item.get("timestamp", 0), reverse=True)
    selected: list[dict[str, Any]] = []
    used_sources: set[str] = set()
    for candidate in candidates:
        if candidate["source"] in used_sources:
            continue
        selected.append(candidate)
        used_sources.add(candidate["source"])
        if len(selected) == 3:
            break
    for candidate in candidates:
        if len(selected) == 3:
            break
        if candidate["id"] not in {item["id"] for item in selected}:
            selected.append(candidate)

    items: list[dict[str, Any]] = []
    for candidate in selected:
        image = ""
        try:
            image = _cache_image(candidate.get("remote_image", ""), candidate["id"])
        except Exception as exc:  # noqa: BLE001
            logger.info("public update image unavailable (%s): %s", candidate["id"], exc)
        items.append(
            {
                key: value
                for key, value in {**candidate, "image": image or candidate["fallback"]}.items()
                if key not in {"remote_image", "fallback", "timestamp"}
            }
        )

    if len(items) < 3:
        known = {item["id"] for item in items}
        items.extend(item for item in DEFAULT_ITEMS if item["id"] not in known)
        items = items[:3]

    now = datetime.now(timezone.utc)
    payload = {
        "items": items,
        "projects": sorted(projects, key=lambda item: item.get("stars", 0), reverse=True),
        "refreshed_at": now.isoformat(),
        "next_refresh_at": (now + timedelta(hours=REFRESH_HOURS)).isoformat(),
        "refresh_hours": REFRESH_HOURS,
        "stale": not bool(candidates),
        "sources": [feed["name"] for feed in FEEDS],
    }
    _write_cache(payload)
    return payload


def get_public_updates() -> dict[str, Any]:
    """Return fresh-enough cached data, refreshing at most once per TTL window."""
    with _CACHE_LOCK:
        cache = _read_cache()
        if cache and _cache_is_fresh(cache):
            return cache
        try:
            return _refresh()
        except Exception as exc:  # noqa: BLE001
            logger.warning("public AI updates refresh failed: %s", exc)
            if cache:
                return {**cache, "stale": True, "refresh_error": str(exc)}
            now = datetime.now(timezone.utc)
            return {
                "items": DEFAULT_ITEMS,
                "projects": [],
                "refreshed_at": now.isoformat(),
                "next_refresh_at": (now + timedelta(hours=REFRESH_HOURS)).isoformat(),
                "refresh_hours": REFRESH_HOURS,
                "stale": True,
                "sources": [feed["name"] for feed in FEEDS],
            }


def update_image_path(item_id: str) -> Path | None:
    if not re.fullmatch(r"update-[0-9a-f]{16}", item_id or ""):
        return None
    path = IMAGE_DIR / f"{item_id}.webp"
    return path if path.is_file() else None
