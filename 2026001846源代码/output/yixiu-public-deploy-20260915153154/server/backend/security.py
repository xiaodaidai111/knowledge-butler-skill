"""Shared security guards for AIOS, MiniClaw, and monitor endpoints."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterable

from flask import g, jsonify, request

from utils import decode_token

BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
SECURITY_DB_PATH = DATA_DIR / "security_audit.db"

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_AUDITOR = "auditor"
WRITE_ROLES = {ROLE_ADMIN, ROLE_OPERATOR}
AUDIT_ROLES = {ROLE_ADMIN, ROLE_OPERATOR, ROLE_AUDITOR}


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _security_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SECURITY_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS security_audit_events (
          id TEXT PRIMARY KEY,
          user_id TEXT,
          role TEXT,
          action TEXT NOT NULL,
          resource TEXT NOT NULL,
          status TEXT NOT NULL,
          request_id TEXT,
          idempotency_key TEXT,
          payload_hash TEXT,
          detail_json TEXT DEFAULT '{}',
          ip_address TEXT,
          user_agent TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS idempotency_records (
          idempotency_key TEXT PRIMARY KEY,
          user_id TEXT,
          action TEXT NOT NULL,
          resource TEXT NOT NULL,
          payload_hash TEXT NOT NULL,
          response_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        """
    )
    return conn


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _request_payload() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    if request.form:
        return {key: request.form.get(key) for key in request.form.keys()}
    return {}


def current_actor() -> dict[str, str]:
    actor = getattr(g, "actor", None) or {}
    return {
        "user_id": str(actor.get("user_id") or "anonymous"),
        "role": str(actor.get("role") or ""),
    }


def get_request_id() -> str:
    request_id = request.headers.get("X-Request-ID") or getattr(g, "request_id", None)
    if not request_id:
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        g.request_id = request_id
    return request_id


def audit_event(
    action: str,
    resource: str,
    status: str,
    detail: dict[str, Any] | None = None,
    idempotency_key: str = "",
    payload: Any = None,
) -> None:
    actor = current_actor()
    try:
        with _security_db() as conn:
            conn.execute(
                """INSERT INTO security_audit_events
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    f"audit-{uuid.uuid4().hex[:16]}",
                    actor["user_id"],
                    actor["role"],
                    action,
                    resource,
                    status,
                    get_request_id(),
                    idempotency_key,
                    payload_hash(payload) if payload is not None else "",
                    _json(detail or {}),
                    request.remote_addr or "",
                    request.headers.get("User-Agent", ""),
                    _now(),
                ),
            )
    except Exception:
        # Audit must not leak internals or break read-only status endpoints.
        pass


def require_jwt_roles(roles: Iterable[str]) -> Callable:
    allowed = set(roles)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization", "")
            if token.startswith("Bearer "):
                token = token[7:]
            payload = decode_token(token) if token else None
            if not payload:
                audit_event("auth", request.path, "denied", {"reason": "missing_or_invalid_token"})
                return jsonify({"code": 401, "message": "missing or invalid token"}), 401

            role = str(payload.get("role") or payload.get("scope") or ROLE_OPERATOR)
            g.actor = {"user_id": payload.get("user_id"), "role": role, "claims": payload}
            if role not in allowed:
                audit_event("auth", request.path, "denied", {"reason": "role_forbidden", "required": sorted(allowed)})
                return jsonify({"code": 403, "message": "permission denied"}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator


def authorize_current_request(roles: Iterable[str]):
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token[7:]
    payload = decode_token(token) if token else None
    if not payload:
        audit_event("auth", request.path, "denied", {"reason": "missing_or_invalid_token"})
        return jsonify({"code": 401, "message": "missing or invalid token"}), 401

    allowed = set(roles)
    role = str(payload.get("role") or payload.get("scope") or ROLE_OPERATOR)
    g.actor = {"user_id": payload.get("user_id"), "role": role, "claims": payload}
    if role not in allowed:
        audit_event("auth", request.path, "denied", {"reason": "role_forbidden", "required": sorted(allowed)})
        return jsonify({"code": 403, "message": "permission denied"}), 403
    return None


def validate_confirmed_write(action: str, resource: str):
    data = _request_payload()
    confirmed = data.get("confirmed") is True or data.get("confirm") is True
    idempotency_key = request.headers.get("Idempotency-Key") or str(data.get("idempotency_key") or "").strip()
    if not confirmed:
        audit_event(action, resource, "denied", {"reason": "confirmation_required"}, payload=data)
        return jsonify({"code": 409, "message": "write operation requires confirmed=true"}), 409
    if not idempotency_key:
        audit_event(action, resource, "denied", {"reason": "idempotency_key_required"}, payload=data)
        return jsonify({"code": 400, "message": "write operation requires Idempotency-Key"}), 400
    return None


def begin_confirmed_write(action: str, resource: str):
    data = _request_payload()
    confirmed = data.get("confirmed") is True or data.get("confirm") is True
    idempotency_key = request.headers.get("Idempotency-Key") or str(data.get("idempotency_key") or "").strip()
    if not confirmed:
        audit_event(action, resource, "denied", {"reason": "confirmation_required"}, payload=data)
        return (jsonify({"code": 409, "message": "write operation requires confirmed=true"}), 409), None
    if not idempotency_key:
        audit_event(action, resource, "denied", {"reason": "idempotency_key_required"}, payload=data)
        return (jsonify({"code": 400, "message": "write operation requires Idempotency-Key"}), 400), None

    digest = payload_hash(data)
    actor = current_actor()
    with _security_db() as conn:
        existing = conn.execute(
            "SELECT * FROM idempotency_records WHERE idempotency_key=?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            if existing["payload_hash"] != digest:
                audit_event(action, resource, "denied", {"reason": "idempotency_conflict"}, idempotency_key, data)
                return (jsonify({"code": 409, "message": "idempotency key reused with different payload"}), 409), None
            cached = json.loads(existing["response_json"] or "{}")
            audit_event(action, resource, "replayed", {}, idempotency_key, data)
            return (jsonify(cached.get("body", {})), int(cached.get("status", 200))), None

    return None, {
        "idempotency_key": idempotency_key,
        "payload_hash": digest,
        "actor": actor,
        "action": action,
        "resource": resource,
        "payload": data,
    }


def complete_confirmed_write(context: dict[str, Any], response: Any):
    flask_response, status = _normalize_response(response)
    body = flask_response.get_json(silent=True) or {}
    with _security_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO idempotency_records
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                context["idempotency_key"],
                context["actor"]["user_id"],
                context["action"],
                context["resource"],
                context["payload_hash"],
                _json({"body": body, "status": status}),
                _now(),
                _now(),
            ),
        )
    audit_event(
        context["action"],
        context["resource"],
        "allowed",
        {"status_code": status},
        context["idempotency_key"],
        context.get("payload"),
    )
    return response


def store_confirmed_write_body(context: dict[str, Any], body: dict[str, Any], status: int = 200) -> None:
    with _security_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO idempotency_records
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                context["idempotency_key"],
                context["actor"]["user_id"],
                context["action"],
                context["resource"],
                context["payload_hash"],
                _json({"body": body, "status": status}),
                _now(),
                _now(),
            ),
        )
    audit_event(
        context["action"],
        context["resource"],
        "allowed",
        {"status_code": status},
        context["idempotency_key"],
        context.get("payload"),
    )


def require_confirmed_write(action: str, resource: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = _request_payload()
            confirmed = data.get("confirmed") is True or data.get("confirm") is True
            idempotency_key = request.headers.get("Idempotency-Key") or str(data.get("idempotency_key") or "").strip()
            if not confirmed:
                audit_event(action, resource, "denied", {"reason": "confirmation_required"}, payload=data)
                return jsonify({"code": 409, "message": "write operation requires confirmed=true"}), 409
            if not idempotency_key:
                audit_event(action, resource, "denied", {"reason": "idempotency_key_required"}, payload=data)
                return jsonify({"code": 400, "message": "write operation requires Idempotency-Key"}), 400

            digest = payload_hash(data)
            actor = current_actor()
            with _security_db() as conn:
                existing = conn.execute(
                    "SELECT * FROM idempotency_records WHERE idempotency_key=?",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    if existing["payload_hash"] != digest:
                        audit_event(action, resource, "denied", {"reason": "idempotency_conflict"}, idempotency_key, data)
                        return jsonify({"code": 409, "message": "idempotency key reused with different payload"}), 409
                    cached = json.loads(existing["response_json"] or "{}")
                    audit_event(action, resource, "replayed", {}, idempotency_key, data)
                    return jsonify(cached.get("body", {})), int(cached.get("status", 200))

                response = func(*args, **kwargs)
                flask_response, status = _normalize_response(response)
                body = flask_response.get_json(silent=True) or {}
                conn.execute(
                    """INSERT INTO idempotency_records
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        idempotency_key,
                        actor["user_id"],
                        action,
                        resource,
                        digest,
                        _json({"body": body, "status": status}),
                        _now(),
                        _now(),
                    ),
                )
                audit_event(action, resource, "allowed", {"status_code": status}, idempotency_key, data)
                return response

        return wrapper

    return decorator


def _normalize_response(response: Any):
    if isinstance(response, tuple):
        return response[0], response[1]
    return response, getattr(response, "status_code", 200)
