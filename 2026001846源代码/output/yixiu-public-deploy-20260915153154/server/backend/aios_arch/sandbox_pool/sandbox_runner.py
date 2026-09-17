"""Sandbox 代码执行池（E2B / agentOS 接口契约本地实现）。

不部署真 E2B，用 subprocess + timeout 在子进程跑用户代码。
Windows 无 setrlimit，故仅做 CPU 时间墙 timeout；POSIX 上额外加 RLIMIT_AS。
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("aios_arch.sandbox_pool")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
SANDBOX_DB_PATH = DATA_DIR / "aios_sandbox.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sandbox_runs (
  id TEXT PRIMARY KEY,
  language TEXT NOT NULL,
  code TEXT NOT NULL,
  stdout TEXT DEFAULT '',
  stderr TEXT DEFAULT '',
  exit_code INTEGER,
  duration_ms INTEGER,
  timed_out INTEGER DEFAULT 0,
  memory_limit_mb INTEGER,
  created_at TEXT NOT NULL
);
"""

_MEMORY_LIMITS = {"python": 256, "javascript": 128, "bash": 64}


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SANDBOX_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _build_preexec(memory_limit_mb: int):
    """POSIX 上设置子进程内存上限；Windows 返回 None。"""
    if os.name != "posix" or not memory_limit_mb:
        return None
    try:
        import resource
        limit_bytes = memory_limit_mb * 1024 * 1024
        def _preexec():
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        return _preexec
    except Exception:  # noqa: BLE001
        return None


def run_code(code: str, language: str = "python", timeout: int = 10,
             memory_limit_mb: Optional[int] = None, stdin: str = "") -> dict:
    run_id = f"sand-{uuid.uuid4().hex[:16]}"
    lang = (language or "python").lower()
    mem_limit = memory_limit_mb or _MEMORY_LIMITS.get(lang, 128)

    if lang == "python":
        cmd = [sys.executable, "-c", code]
    elif lang in {"bash", "sh"}:
        cmd = ["bash", "-c", code] if os.name == "posix" else ["cmd.exe", "/c", code]
    elif lang == "javascript":
        cmd = ["node", "-e", code]
    else:
        result = {
            "id": run_id, "language": lang, "code": code, "stdout": "", "stderr": "",
            "exit_code": 2, "duration_ms": 0, "timed_out": False,
            "error": f"unsupported language: {lang}",
        }
        _persist(result)
        return result

    preexec = _build_preexec(mem_limit)
    started = datetime.utcnow()
    timed_out = False
    try:
        proc = subprocess.run(
            cmd, input=stdin, capture_output=True, text=True,
            timeout=timeout, preexec_fn=preexec,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\n[timed out after {timeout}s]"
        exit_code = 124
        timed_out = True
    except Exception as exc:  # noqa: BLE001
        stdout = ""
        stderr = f"[sandbox error] {exc}"
        exit_code = 125

    duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
    result = {
        "id": run_id, "language": lang, "code": code,
        "stdout": stdout, "stderr": stderr, "exit_code": exit_code,
        "duration_ms": duration_ms, "timed_out": timed_out,
        "memory_limit_mb": mem_limit,
    }
    _persist(result)
    return result


def _persist(result: dict) -> None:
    try:
        with _db() as conn:
            conn.execute(
                "INSERT INTO sandbox_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (result["id"], result["language"], result["code"],
                 result.get("stdout", ""), result.get("stderr", ""),
                 result.get("exit_code"), result.get("duration_ms", 0),
                 1 if result.get("timed_out") else 0,
                 result.get("memory_limit_mb"), _now()),
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("sandbox persist failed: %s", exc)


def list_runs(limit: int = 50) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM sandbox_runs ORDER BY created_at DESC LIMIT ?", (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_run(run_id: str) -> Optional[dict]:
    with _db() as conn:
        row = conn.execute("SELECT * FROM sandbox_runs WHERE id=?", (run_id,)).fetchone()
        return dict(row) if row else None


def reset_for_tests(db_path: Optional[Path] = None) -> None:
    global SANDBOX_DB_PATH
    target = db_path or SANDBOX_DB_PATH
    if target.exists():
        target.unlink()
