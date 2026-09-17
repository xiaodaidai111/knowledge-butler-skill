"""Mem0 风格的本地记忆层。

无真 embedding 模型时使用 sha256 滑窗哈希作为伪 embedding（128 维），
保证同语义词汇在相同窗口下向量一致；命中后用 Jaccard 相似度排序。
若检测到 rag_service 已有 embedding，可附加真向量。

接口对齐 Mem0 REST：
- POST /v1/memories/  -> add(user_id, agent_id, content, metadata)
- GET  /v1/memories/?user_id=...&q=... -> search
- GET  /v1/memories/{id} -> get
- PUT  /v1/memories/{id}/ -> update
- DELETE /v1/memories/{id}/ -> delete
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("aios_arch.memory_layer")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
MEMORY_DB_PATH = DATA_DIR / "aios_memory.db"
EMBEDDING_DIM = 128
_WORD_RE = re.compile(r"[A-Za-z0-9_]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _tokens(text: str) -> list[str]:
    """ASCII 词整词切分；中文按单字 + bigram 切分，保证字符重叠可被余弦捕获。"""
    if not text:
        return []
    out: list[str] = []
    out.extend(t.lower() for t in _WORD_RE.findall(text))
    cjk_chars = _CJK_RE.findall(text)
    # 单字：保证相同字符命中
    out.extend(cjk_chars)
    # bigram：保留短句局部共现信息
    for i in range(len(cjk_chars) - 1):
        out.append(cjk_chars[i] + cjk_chars[i + 1])
    return out


_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_items (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata_json TEXT DEFAULT '{}',
  embedding_json TEXT,
  score REAL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  expired_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_mem_user ON memory_items(user_id);
CREATE INDEX IF NOT EXISTS idx_mem_agent ON memory_items(agent_id);
CREATE TABLE IF NOT EXISTS memory_sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  summary TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t]


def embed(text: str) -> list[float]:
    """滑窗 sha256 哈希伪 embedding：128 维 [0,1) 浮点向量。"""
    tokens = _tokens(text)
    if not tokens:
        return [0.0] * EMBEDDING_DIM
    vec = [0.0] * EMBEDDING_DIM
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        for i in range(EMBEDDING_DIM):
            vec[i] += (h[i % len(h)] / 255.0)
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb + 1e-9)


def add(user_id: str, agent_id: str, content: str,
        metadata: Optional[dict] = None, embedding: Optional[list[float]] = None) -> str:
    if not content:
        return ""
    mem_id = f"mem-{uuid.uuid4().hex[:16]}"
    emb = embedding or embed(content)
    with _db() as conn:
        conn.execute(
            "INSERT INTO memory_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mem_id, user_id, agent_id, content,
             json.dumps(metadata or {}, ensure_ascii=False),
             json.dumps(emb), 0.0, _now(), _now(), None),
        )
    logger.info("memory add %s user=%s agent=%s", mem_id, user_id, agent_id)
    return mem_id


def search(user_id: str, query: str, agent_id: str = "", top_k: int = 5,
           min_score: float = 0.0) -> list[dict]:
    if not query:
        return []
    qvec = embed(query)
    with _db() as conn:
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM memory_items WHERE user_id=? AND agent_id=? ORDER BY created_at DESC",
                (user_id, agent_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memory_items WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        scored: list[dict] = []
        for r in rows:
            try:
                vec = json.loads(r["embedding_json"] or "[]")
            except Exception:  # noqa: BLE001
                vec = []
            score = cosine(qvec, vec) if vec else 0.0
            if score >= min_score:
                item = dict(r)
                item["score"] = score
                item["metadata"] = json.loads(r["metadata_json"] or "{}")
                scored.append(item)
        scored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return scored[:top_k]


def get(memory_id: str) -> Optional[dict]:
    with _db() as conn:
        row = conn.execute("SELECT * FROM memory_items WHERE id=?", (memory_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["metadata"] = json.loads(row["metadata_json"] or "{}")
        return item


def list_memories(user_id: str, agent_id: str = "", limit: int = 50) -> list[dict]:
    with _db() as conn:
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM memory_items WHERE user_id=? AND agent_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, agent_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memory_items WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]


def update(memory_id: str, content: str = "", metadata: Optional[dict] = None) -> bool:
    with _db() as conn:
        row = conn.execute("SELECT * FROM memory_items WHERE id=?", (memory_id,)).fetchone()
        if not row:
            return False
        new_content = content or row["content"]
        merged_meta = json.loads(row["metadata_json"] or "{}")
        if metadata:
            merged_meta.update(metadata)
        emb = embed(new_content)
        conn.execute(
            "UPDATE memory_items SET content=?, metadata_json=?, embedding_json=?, updated_at=? WHERE id=?",
            (new_content, json.dumps(merged_meta, ensure_ascii=False),
             json.dumps(emb), _now(), memory_id),
        )
        return True


def delete(memory_id: str) -> bool:
    with _db() as conn:
        cur = conn.execute("DELETE FROM memory_items WHERE id=?", (memory_id,))
        return cur.rowcount > 0


def reset_for_tests(db_path: Optional[Path] = None) -> None:
    global MEMORY_DB_PATH
    target = db_path or MEMORY_DB_PATH
    if target.exists():
        target.unlink()
