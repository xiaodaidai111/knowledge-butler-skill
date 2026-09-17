# -*- coding: utf-8 -*-
"""
统一 API 响应格式，便于前端统一处理。
约定：code=0 表示成功，code 非 0 表示业务或参数错误，HTTP 4xx/5xx 仍由 Flask 返回。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import jsonify

# 业务错误码（与 HTTP 状态码分离，便于前端区分）
CODE_OK = 0
CODE_BAD_REQUEST = 400
CODE_UNAUTHORIZED = 401
CODE_NOT_FOUND = 404
CODE_SERVER_ERROR = 500


def api_success(data: Any, message: str = "ok") -> Tuple[Dict[str, Any], int]:
    """成功响应：{ "code": 0, "message": "ok", "data": data, "time": "ISO8601" }。"""
    return (
        jsonify({
            "code": CODE_OK,
            "message": message,
            "data": data,
            "time": datetime.utcnow().isoformat() + "Z",
        }),
        200,
    )


def api_error(
    message: str,
    code: int = CODE_BAD_REQUEST,
    data: Optional[Any] = None,
) -> Tuple[Dict[str, Any], int]:
    """错误响应：{ "code": code, "message": message, "data": data, "time": "ISO8601" }。"""
    return (
        jsonify({
            "code": code,
            "message": message,
            "data": data,
            "time": datetime.utcnow().isoformat() + "Z",
        }),
        200,  # 业务错误仍返回 200，由前端根据 code 判断
    )


def api_error_http(message: str, http_status: int = 400) -> Tuple[Dict[str, Any], int]:
    """HTTP 级错误：同时设置 code 与 HTTP 状态码，用于参数错误、未授权等。"""
    code = CODE_BAD_REQUEST
    if http_status == 401:
        code = CODE_UNAUTHORIZED
    elif http_status == 404:
        code = CODE_NOT_FOUND
    elif http_status >= 500:
        code = CODE_SERVER_ERROR
    return (
        jsonify({
            "code": code,
            "message": message,
            "data": None,
            "time": datetime.utcnow().isoformat() + "Z",
        }),
        http_status,
    )
