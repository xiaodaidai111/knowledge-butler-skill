import bcrypt
import logging
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, request

from utils import (
    decode_token,
    error_response,
    generate_token,
    get_db_connection,
    success_response,
    token_required,
    validate_required_fields,
)


auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _parse_json() -> dict:
    return request.get_json(silent=True) or {}


@auth_bp.route("/guest/create", methods=["POST"])
def create_guest_session():
    """创建游客会话（不要求登录）"""
    try:
        data = _parse_json()
        device_info = data.get("device_info") or {}
        ip_address = request.remote_addr or ""
        user_agent = request.headers.get("User-Agent", "")

        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO guest_sessions (session_id, device_info, ip_address, user_agent, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, str(device_info), ip_address, user_agent, expires_at),
            )
            conn.commit()

        return success_response(
            {
                "session_id": session_id,
                "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                "is_guest": True,
            },
            "游客会话创建成功",
        )
    except Exception as e:
        logger.exception("创建游客会话失败")
        return error_response(500, f"创建游客会话失败：{str(e)}")


@auth_bp.route("/guest/verify", methods=["GET"])
def verify_guest_session():
    """验证游客会话（不要求登录）"""
    try:
        session_id = request.args.get("session_id", "").strip()
        if not session_id:
            return error_response(400, "缺少session_id参数")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT session_id, expires_at, created_at
                FROM guest_sessions
                WHERE session_id = %s AND expires_at > NOW()
                """,
                (session_id,),
            )
            session = cursor.fetchone()

        if not session:
            return error_response(401, "游客会话无效或已过期")

        return success_response(
            {
                "valid": True,
                "session_id": session["session_id"],
                "expires_at": session["expires_at"].strftime("%Y-%m-%d %H:%M:%S"),
            },
            "游客会话有效",
        )
    except Exception as e:
        logger.exception("验证游客会话失败")
        return error_response(500, f"验证失败：{str(e)}")


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
    try:
        data = _parse_json()
        if not data:
            return error_response(400, "请求数据格式错误")

        phone = (data.get("phone") or "").strip()
        password = data.get("password") or ""
        name = (data.get("name") or "").strip()

        is_valid, error_msg = validate_required_fields(data, ["phone", "password", "name"])
        if not is_valid:
            return error_response(400, error_msg)

        if len(phone) != 11:
            return error_response(400, "手机号格式不正确")
        if len(password) < 6:
            return error_response(400, "密码长度不能少于6位")
        if len(name) < 2:
            return error_response(400, "用户名长度不能少于2位")

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1) 检查手机号是否已注册
            cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
            if cursor.fetchone():
                return error_response(400, "该手机号已注册")

            # 2) 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE name = %s", (name,))
            if cursor.fetchone():
                return error_response(400, "该用户名已被使用")

            # 3) 密码加密
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # 4) 创建用户
            cursor.execute(
                """
                INSERT INTO users (phone, password_hash, name, level, level_name, is_guest, status)
                VALUES (%s, %s, %s, 1, '新手', 0, 'active')
                """,
                (phone, password_hash, name),
            )
            user_id = cursor.lastrowid

            # 先提交用户主数据，后续可选表写入失败不应影响注册成功
            conn.commit()

            # 5) 默认用户设置
            try:
                cursor.execute(
                    """
                    INSERT INTO user_settings (user_id, theme, language, notifications_enabled, privacy_level)
                    VALUES (%s, 'light', 'zh-CN', 1, 'normal')
                    """,
                    (user_id,),
                )
                conn.commit()
            except Exception:
                # 允许“注册成功但未写入默认设置”的降级（不阻塞注册）
                pass

            # 6) 默认用户偏好（用于个性化）
            try:
                cursor.execute(
                    """
                    INSERT INTO user_preferences
                        (user_id, allergies, favorite_cuisines, dietary_habits, custom_notes, cooking_exp)
                    VALUES (%s, NULL, NULL, NULL, NULL, 0)
                    """,
                    (user_id,),
                )
                conn.commit()
            except Exception:
                # 偏好表缺失也不阻塞注册主流程
                pass

            # 7) 写登录历史（注册视为一次成功登录）
            token = generate_token(user_id)
            if isinstance(token, bytes):
                token = token.decode("utf-8")

            try:
                cursor.execute(
                    """
                    INSERT INTO login_history (user_id, ip_address, device_info, login_type, status, login_time)
                    VALUES (%s, %s, %s, 'password', 'success', CURRENT_TIMESTAMP)
                    """,
                    (
                        user_id,
                        request.remote_addr or "",
                        str(request.headers.get("User-Agent", "")),
                    ),
                )
                conn.commit()
            except Exception:
                pass

        return success_response(
            {
                "token": token,
                "user": {
                    "id": user_id,
                    "name": name,
                    "phone": phone,
                    "level": 1,
                    "level_name": "新手",
                },
            },
            "注册成功",
        )
    except Exception as e:
        logger.exception("注册异常")
        return error_response(500, f"注册失败：{str(e)}")


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录"""
    try:
        data = _parse_json()
        if not data:
            return error_response(400, "请求数据格式错误")

        phone = (data.get("phone") or "").strip()
        password = data.get("password") or ""

        is_valid, error_msg = validate_required_fields(data, ["phone", "password"])
        if not is_valid:
            return error_response(400, error_msg)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 尝试完整字段查询（含检修岗位信息字段）
            for stmt in [
                """
                SELECT id, password_hash, name, avatar, level, level_name, status, is_guest,
                       gender, age, height, weight, bio, phone,
                       department, position, specialty, skill_level, certifications, employee_id
                FROM users WHERE phone = %s
                """,
                """
                SELECT id, password_hash, name, avatar, level, level_name, status, is_guest,
                       gender, age, height, weight, bio, phone
                FROM users WHERE phone = %s
                """,
                """
                SELECT id, password_hash, name, avatar, level, level_name, status, is_guest
                FROM users WHERE phone = %s
                """,
            ]:
                try:
                    cursor.execute(stmt, (phone,))
                    user = cursor.fetchone()
                    break
                except Exception:
                    user = None
            if user:
                for field in ["gender", "age", "height", "weight", "bio", "phone",
                              "department", "position", "specialty", "skill_level",
                              "certifications", "employee_id"]:
                    user.setdefault(field, None)

            if not user:
                # 登录失败记录（不影响登录流程）
                try:
                    cursor.execute(
                        """
                        INSERT INTO login_history (user_id, ip_address, device_info, login_type, status, login_time)
                        VALUES (NULL, %s, %s, 'password', 'failed', CURRENT_TIMESTAMP)
                        """,
                        (request.remote_addr or "", str(request.headers.get("User-Agent", ""))),
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                return error_response(401, "手机号或密码错误")

            if user.get("status") != "active":
                return error_response(403, "账号已被禁用")

            if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                try:
                    cursor.execute(
                        """
                        INSERT INTO login_history (user_id, ip_address, device_info, login_type, status, login_time)
                        VALUES (%s, %s, %s, 'password', 'failed', CURRENT_TIMESTAMP)
                        """,
                        (
                            user["id"],
                            request.remote_addr or "",
                            str(request.headers.get("User-Agent", "")),
                        ),
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                return error_response(401, "手机号或密码错误")

            token = generate_token(user["id"])
            if isinstance(token, bytes):
                token = token.decode("utf-8")

            # 写登录成功记录
            try:
                cursor.execute(
                    """
                    INSERT INTO login_history (user_id, ip_address, device_info, login_type, status, login_time)
                    VALUES (%s, %s, %s, 'password', 'success', CURRENT_TIMESTAMP)
                    """,
                    (
                        user["id"],
                        request.remote_addr or "",
                        str(request.headers.get("User-Agent", "")),
                    ),
                )
                conn.commit()
            except Exception:
                conn.rollback()

            # 更新最后登录时间（不强依赖）
            try:
                cursor.execute(
                    "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (user["id"],),
                )
                conn.commit()
            except Exception:
                conn.rollback()

        return success_response(
            {
                "token": token,
                "user": {
                    "id": user["id"],
                    "name": user.get("name"),
                    "phone": phone,
                    "avatar": user.get("avatar"),
                    "level": user.get("level"),
                    "level_name": user.get("level_name"),
                    "gender": user.get("gender"),
                    "age": user.get("age"),
                    "height": user.get("height"),
                    "weight": user.get("weight"),
                    "bio": user.get("bio"),
                    "department": user.get("department"),
                    "position": user.get("position"),
                    "specialty": user.get("specialty"),
                    "skill_level": user.get("skill_level"),
                    "certifications": user.get("certifications"),
                    "employee_id": user.get("employee_id"),
                },
            },
            "登录成功",
        )
    except Exception as e:
        logger.exception("登录异常")
        return error_response(500, f"登录失败：{str(e)}")


@auth_bp.route("/verify", methods=["GET"])
def verify_token():
    """验证token（可选接口）"""
    token = request.args.get("token", "").strip()
    if not token:
        return error_response(400, "缺少token参数")

    payload = decode_token(token)
    if not payload:
        return error_response(401, "Token无效或已过期")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for stmt in [
            """
            SELECT id, name, phone, avatar, level, level_name, status,
                   gender, age, height, weight, bio,
                   department, position, specialty, skill_level, certifications, employee_id
            FROM users WHERE id = %s
            """,
            """
            SELECT id, name, phone, avatar, level, level_name, status, gender, age, height, weight, bio
            FROM users WHERE id = %s
            """,
            """
            SELECT id, name, phone, avatar, level, level_name, status
            FROM users WHERE id = %s
            """,
        ]:
            try:
                cursor.execute(stmt, (payload["user_id"],))
                user = cursor.fetchone()
                break
            except Exception:
                user = None
        if user:
            for field in ["gender", "age", "height", "weight", "bio", "department",
                          "position", "specialty", "skill_level", "certifications", "employee_id"]:
                user.setdefault(field, None)

    if not user or user.get("status") != "active":
        return error_response(404, "用户不存在或已被禁用")

    return success_response(
        {
            "valid": True,
            "user": {
                "id": user["id"],
                "name": user.get("name"),
                "phone": user.get("phone"),
                "avatar": user.get("avatar"),
                "level": user.get("level"),
                "level_name": user.get("level_name"),
                "gender": user.get("gender"),
                "age": user.get("age"),
                "height": user.get("height"),
                "weight": user.get("weight"),
                "bio": user.get("bio"),
                "department": user.get("department"),
                "position": user.get("position"),
                "specialty": user.get("specialty"),
                "skill_level": user.get("skill_level"),
                "certifications": user.get("certifications"),
                "employee_id": user.get("employee_id"),
            },
        },
        "Token有效",
    )


@auth_bp.route("/check-username", methods=["POST"])
def check_username():
    """检查用户名是否可用"""
    try:
        data = _parse_json()
        name = (data.get("name") or "").strip()
        if not name:
            return error_response(400, "用户名不能为空")
        if len(name) < 2:
            return error_response(400, "用户名长度不能少于2位")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE name = %s", (name,))
            exists = cursor.fetchone() is not None

        return success_response({"available": not exists}, "用户名检查完成")
    except Exception as e:
        logger.exception("检查用户名异常")
        return error_response(500, f"检查失败：{str(e)}")


@auth_bp.route("/check-phone", methods=["POST"])
def check_phone():
    """检查手机号是否已注册"""
    try:
        data = _parse_json()
        phone = (data.get("phone") or "").strip()
        if not phone:
            return error_response(400, "手机号不能为空")
        if len(phone) != 11:
            return error_response(400, "手机号格式不正确")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
            registered = cursor.fetchone() is not None

        return success_response({"registered": registered}, "手机号检查完成")
    except Exception as e:
        logger.exception("检查手机号异常")
        return error_response(500, f"检查失败：{str(e)}")


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    """用户退出登录（前端通常只移除token，因此此接口为幂等）"""
    return success_response(None, "退出登录成功")

