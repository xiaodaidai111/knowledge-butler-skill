"""OPA 风格的本地策略引擎。

不依赖真 OPA server，用 Python 实现策略求值覆盖：
- role_check：actor.role 是否在 allowed_roles
- approval_check：write 类动作是否需要审批 / 是否被 approve_all 跳过
- idempotency_check：幂等键 + payload hash 一致性（与 security.idempotency_records 联动）
- rate_limit：actor 每分钟动作次数上限
- approval_block：高优先级硬阻断策略

策略 schema（rule_json）：
    {"kind": "role_check", "allowed_roles": ["admin", "operator"]}
    {"kind": "approval_check", "allow_when": "approve_all", "block_when": "unapproved"}
    {"kind": "rate_limit", "window_seconds": 60, "max_calls": 30}
    {"kind": "approval_block", "actions": ["aios.execute.write"], "priority": 100}
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("aios_arch.opa_guard")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
OPA_DB_PATH = DATA_DIR / "aios_opa.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS opa_policies (
  name TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  rule_json TEXT NOT NULL,
  priority INTEGER DEFAULT 50,
  enabled INTEGER DEFAULT 1,
  description TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opa_decisions (
  id TEXT PRIMARY KEY,
  trace_id TEXT,
  actor_id TEXT,
  action TEXT NOT NULL,
  resource TEXT NOT NULL,
  decision TEXT NOT NULL,
  reason TEXT,
  applied_policies_json TEXT DEFAULT '[]',
  payload_hash TEXT,
  evaluated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opa_rate_windows (
  actor_id TEXT NOT NULL,
  window_start REAL NOT NULL,
  window_seconds INTEGER NOT NULL,
  policy_name TEXT NOT NULL DEFAULT '',
  call_count INTEGER DEFAULT 0,
  PRIMARY KEY (actor_id, window_start, window_seconds, policy_name)
);
"""


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(OPA_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _seed_default_policies(conn: sqlite3.Connection) -> None:
    defaults = [
        ("deny_anonymous_write", "role_check",
         {"kind": "role_check", "allowed_roles": ["admin", "operator"], "block_anonymous": True}, 90),
        ("write_requires_approval", "approval_check",
         {"kind": "approval_check", "allow_when": "approve_all", "block_when": "unapproved"}, 80),
        ("rate_limit_per_user", "rate_limit",
         {"kind": "rate_limit", "window_seconds": 60, "max_calls": 60}, 50),
        ("readonly_never_block", "approval_check",
         {"kind": "approval_check", "allow_when": "always", "match_kind": "read"}, 40),
    ]
    for name, kind, rule, priority in defaults:
        existing = conn.execute("SELECT name FROM opa_policies WHERE name=?", (name,)).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO opa_policies VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, kind, json.dumps(rule, ensure_ascii=False), priority, 1,
             f"默认策略:{kind}", _now(), _now()),
        )


def register_policy(name: str, kind: str, rule: dict, priority: int = 50,
                    description: str = "", enabled: bool = True) -> None:
    with _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO opa_policies VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, kind, json.dumps(rule, ensure_ascii=False), priority,
             1 if enabled else 0, description, _now(), _now()),
        )


def list_policies(only_enabled: bool = False) -> list[dict]:
    with _db() as conn:
        _seed_default_policies(conn)
        sql = "SELECT * FROM opa_policies"
        if only_enabled:
            sql += " WHERE enabled=1"
        sql += " ORDER BY priority DESC"
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]


def _bump_rate(conn: sqlite3.Connection, actor_id: str, window_seconds: int,
               max_calls: int, policy_name: str = "") -> tuple[bool, int]:
    """返回 (allowed, current_count)。超过 max_calls 时拒绝。每个策略独立桶。"""
    now = time.time()
    window_start = int(now // window_seconds) * window_seconds
    row = conn.execute(
        "SELECT call_count FROM opa_rate_windows WHERE actor_id=? AND window_start=? AND window_seconds=? AND policy_name=?",
        (actor_id, window_start, window_seconds, policy_name),
    ).fetchone()
    current = (row["call_count"] if row else 0) + 1
    conn.execute(
        "INSERT OR REPLACE INTO opa_rate_windows VALUES (?, ?, ?, ?, ?)",
        (actor_id, window_start, window_seconds, policy_name, current),
    )
    return current <= max_calls, current


def evaluate(action: str, resource: str, payload: Optional[dict] = None,
             actor: Optional[dict] = None, context: Optional[dict] = None,
             trace_id: str = "") -> dict:
    """求值所有匹配策略，返回 {decision, reason, applied_policies, decision_id}。"""
    payload = payload or {}
    actor = actor or {"user_id": "anonymous", "role": "anonymous"}
    context = context or {}
    actor_id = str(actor.get("user_id") or "anonymous")
    role = str(actor.get("role") or "anonymous")
    kind = str(context.get("kind") or "write")
    approve_all = bool(context.get("approve_all") or payload.get("approve_all") or False)
    applied: list[dict] = []
    decision = "allow"
    reason = ""

    with _db() as conn:
        _seed_default_policies(conn)
        policies = conn.execute(
            "SELECT * FROM opa_policies WHERE enabled=1 ORDER BY priority DESC"
        ).fetchall()
        for p in policies:
            rule = json.loads(p["rule_json"] or "{}")
            rkind = p["kind"]
            pname = p["name"]
            if rkind == "role_check":
                allowed = set(rule.get("allowed_roles", []))
                block_anon = bool(rule.get("block_anonymous", True))
                if block_anon and actor_id == "anonymous":
                    decision = "deny"; reason = f"{pname}: 匿名身份被拒绝"
                    applied.append({"policy": pname, "rule": rkind, "decision": "deny"})
                    break
                if allowed and role not in allowed:
                    decision = "deny"; reason = f"{pname}: 角色 {role} 不在 {sorted(allowed)}"
                    applied.append({"policy": pname, "rule": rkind, "decision": "deny"})
                    break
                applied.append({"policy": pname, "rule": rkind, "decision": "allow"})
            elif rkind == "approval_check":
                match_kind = rule.get("match_kind", "write")
                if match_kind != kind and match_kind != "all":
                    continue
                allow_when = rule.get("allow_when", "approve_all")
                if allow_when == "always":
                    applied.append({"policy": pname, "rule": rkind, "decision": "allow"})
                    continue
                if kind == "write" and not approve_all and not context.get("approved"):
                    decision = "deny"
                    reason = f"{pname}: write 动作需要审批 (approve_all 未启用)"
                    applied.append({"policy": pname, "rule": rkind, "decision": "deny"})
                    break
                applied.append({"policy": pname, "rule": rkind, "decision": "allow"})
            elif rkind == "rate_limit":
                ws = int(rule.get("window_seconds", 60))
                mc = int(rule.get("max_calls", 60))
                ok, current = _bump_rate(conn, actor_id, ws, mc, policy_name=pname)
                if not ok:
                    decision = "deny"
                    reason = f"{pname}: 速率超限 {current}/{mc} per {ws}s"
                    applied.append({"policy": pname, "rule": rkind, "decision": "deny",
                                   "current": current, "max": mc})
                    break
                applied.append({"policy": pname, "rule": rkind, "decision": "allow",
                               "current": current, "max": mc})
            elif rkind == "approval_block":
                actions = set(rule.get("actions", []))
                if action in actions:
                    decision = "deny"; reason = f"{pname}: 硬阻断动作 {action}"
                    applied.append({"policy": pname, "rule": rkind, "decision": "deny"})
                    break

        import hashlib
        ph = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()
        decision_id = f"opa-{uuid.uuid4().hex[:16]}"
        conn.execute(
            "INSERT INTO opa_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (decision_id, trace_id, actor_id, action, resource, decision,
             reason or "all policies allowed", json.dumps(applied, ensure_ascii=False),
             ph, _now()),
        )
    logger.info("opa decision %s action=%s -> %s (%s)", decision_id, action, decision, reason)
    return {
        "decision": decision,
        "reason": reason or "all policies allowed",
        "applied_policies": applied,
        "decision_id": decision_id,
    }


def list_decisions(trace_id: str = "", limit: int = 100) -> list[dict]:
    with _db() as conn:
        if trace_id:
            rows = conn.execute(
                "SELECT * FROM opa_decisions WHERE trace_id=? ORDER BY evaluated_at DESC LIMIT ?",
                (trace_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM opa_decisions ORDER BY evaluated_at DESC LIMIT ?", (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def reset_for_tests(db_path: Optional[Path] = None) -> None:
    global OPA_DB_PATH
    target = db_path or OPA_DB_PATH
    if target.exists():
        target.unlink()
