"""Langfuse/LangSmith 兼容的本地 trace 落盘。

提供 trace + observation(span/event) 两层模型，schema 对齐 Langfuse REST API：
POST /api/public/ingestion 的 `batch` 字段结构（trace + observation + score）。

落盘：SQLite（server/backend/data/aios_trace.db）。
可选拉取：trace_exporter.export_batch() 返回 Langfuse ingestion 兼容 payload，
配置 AIOS_TRACE_PUSH_URL 后可批量外发（默认不发，仅本地）。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("aios_arch.trace")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
TRACE_DB_PATH = DATA_DIR / "aios_trace.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  user_id TEXT,
  session_id TEXT,
  version TEXT,
  release TEXT,
  metadata_json TEXT DEFAULT '{}',
  input_json TEXT,
  output_json TEXT,
  status TEXT DEFAULT 'running',
  started_at TEXT NOT NULL,
  ended_at TEXT
);
CREATE TABLE IF NOT EXISTS observations (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  parent_id TEXT,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT,
  input_json TEXT,
  output_json TEXT,
  metadata_json TEXT DEFAULT '{}',
  level TEXT DEFAULT 'DEFAULT',
  status TEXT DEFAULT 'running',
  model TEXT,
  cost_total DECIMAL(10,6) DEFAULT 0,
  FOREIGN KEY (trace_id) REFERENCES traces(id)
);
CREATE INDEX IF NOT EXISTS idx_obs_trace ON observations(trace_id);
CREATE INDEX IF NOT EXISTS idx_obs_parent ON observations(parent_id);
CREATE INDEX IF NOT EXISTS idx_traces_started ON traces(started_at);
"""


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(TRACE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def start_trace(name: str, user_id: str = "", session_id: str = "",
                metadata: Optional[dict] = None, input_data: Any = None,
                version: str = "0.1.0", release: str = "local") -> str:
    trace_id = _new_id("trace")
    with _db() as conn:
        conn.execute(
            "INSERT INTO traces VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (trace_id, name, user_id, session_id, version, release,
             json.dumps(metadata or {}, ensure_ascii=False),
             json.dumps(input_data, ensure_ascii=False, default=str) if input_data is not None else None,
             None, "running", _now(), None),
        )
    logger.info("trace start: %s name=%s", trace_id, name)
    return trace_id


def end_trace(trace_id: str, status: str = "completed",
              output_data: Any = None, metadata: Optional[dict] = None) -> None:
    with _db() as conn:
        row = conn.execute("SELECT metadata_json FROM traces WHERE id=?", (trace_id,)).fetchone()
        merged_meta = {}
        if row and row["metadata_json"]:
            try:
                merged_meta = json.loads(row["metadata_json"])
            except Exception:  # noqa: BLE001
                merged_meta = {}
        if metadata:
            merged_meta.update(metadata)
        conn.execute(
            "UPDATE traces SET status=?, ended_at=?, output_json=?, metadata_json=? WHERE id=?",
            (status, _now(),
             json.dumps(output_data, ensure_ascii=False, default=str) if output_data is not None else None,
             json.dumps(merged_meta, ensure_ascii=False), trace_id),
        )


def start_observation(trace_id: str, name: str, type_: str = "span",
                      parent_id: Optional[str] = None,
                      input_data: Any = None, metadata: Optional[dict] = None,
                      model: str = "", level: str = "DEFAULT") -> str:
    obs_id = _new_id("obs")
    with _db() as conn:
        conn.execute(
            "INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (obs_id, trace_id, parent_id, name, type_, _now(), None,
             json.dumps(input_data, ensure_ascii=False, default=str) if input_data is not None else None,
             None, json.dumps(metadata or {}, ensure_ascii=False), level, "running", model, 0),
        )
    return obs_id


def end_observation(obs_id: str, status: str = "completed",
                    output_data: Any = None, metadata: Optional[dict] = None,
                    level: str = "DEFAULT", cost: float = 0.0) -> None:
    with _db() as conn:
        row = conn.execute("SELECT metadata_json FROM observations WHERE id=?", (obs_id,)).fetchone()
        merged_meta = {}
        if row and row["metadata_json"]:
            try:
                merged_meta = json.loads(row["metadata_json"])
            except Exception:  # noqa: BLE001
                merged_meta = {}
        if metadata:
            merged_meta.update(metadata)
        conn.execute(
            "UPDATE observations SET status=?, end_time=?, output_json=?, metadata_json=?, level=?, cost_total=? WHERE id=?",
            (status, _now(),
             json.dumps(output_data, ensure_ascii=False, default=str) if output_data is not None else None,
             json.dumps(merged_meta, ensure_ascii=False), level, cost, obs_id),
        )


def list_traces(limit: int = 50, name_like: str = "") -> list[dict]:
    with _db() as conn:
        sql = "SELECT * FROM traces"
        params: list = []
        if name_like:
            sql += " WHERE name LIKE ?"
            params.append(f"%{name_like}%")
        sql += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_trace(trace_id: str) -> Optional[dict]:
    with _db() as conn:
        row = conn.execute("SELECT * FROM traces WHERE id=?", (trace_id,)).fetchone()
        if not row:
            return None
        trace = dict(row)
        obs_rows = conn.execute(
            "SELECT * FROM observations WHERE trace_id=? ORDER BY start_time", (trace_id,)
        ).fetchall()
        trace["observations"] = [dict(o) for o in obs_rows]
        return trace


def export_batch(limit: int = 100) -> dict:
    """返回 Langfuse ingestion 兼容 payload，便于推送到远端 trace 服务。"""
    with _db() as conn:
        traces = conn.execute(
            "SELECT * FROM traces ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        items: list[dict] = []
        for t in traces:
            tid = t["id"]
            items.append({
                "id": tid, "type": "trace-create",
                "body": {
                    "id": tid, "name": t["name"], "userId": t["user_id"] or None,
                    "sessionId": t["session_id"] or None, "version": t["version"],
                    "release": t["release"],
                    "metadata": json.loads(t["metadata_json"] or "{}"),
                    "input": json.loads(t["input_json"]) if t["input_json"] else None,
                    "output": json.loads(t["output_json"]) if t["output_json"] else None,
                    "timestamp": t["started_at"],
                },
            })
            observations = conn.execute(
                "SELECT * FROM observations WHERE trace_id=?", (tid,)
            ).fetchall()
            for o in observations:
                items.append({
                    "id": o["id"], "type": "observation-create",
                    "body": {
                        "id": o["id"], "traceId": tid, "parentObservationId": o["parent_id"],
                        "name": o["name"], "type": o["type"],
                        "startTime": o["start_time"], "endTime": o["end_time"],
                        "input": json.loads(o["input_json"]) if o["input_json"] else None,
                        "output": json.loads(o["output_json"]) if o["output_json"] else None,
                        "metadata": json.loads(o["metadata_json"] or "{}"),
                        "level": o["level"], "model": o["model"] or None,
                    },
                })
    return {"batch": items, "count": len(items)}


def reset_for_tests(db_path: Optional[Path] = None) -> None:
    """测试钩子：把目标 db 清空。"""
    global TRACE_DB_PATH
    target = db_path or TRACE_DB_PATH
    if target.exists():
        target.unlink()
