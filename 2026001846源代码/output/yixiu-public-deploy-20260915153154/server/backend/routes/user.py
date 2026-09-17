import io
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, abort, request, send_from_directory
from PIL import Image

from utils import error_response, get_db_connection, success_response, token_required, decode_token


user_bp = Blueprint("user", __name__)
logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
AVATAR_MAX_SIZE = (300, 300)  # 头像最大尺寸
AVATAR_THUMBNAIL_SIZE = (100, 100)  # 缩略图尺寸

# Flask 默认静态目录通常是 backend/static，对应 URL 前缀 /static/
BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
STATIC_DIR = BACKEND_DIR / "static"
LEGACY_AVATAR_FOLDER = STATIC_DIR / "uploads" / "avatars"
DEFAULT_AVATAR_UPLOAD_ROOT = PROJECT_ROOT / "uploads"
AVATAR_UPLOAD_ROOT = Path(os.getenv("AVATAR_UPLOAD_ROOT", str(DEFAULT_AVATAR_UPLOAD_ROOT))).expanduser()
UPLOAD_FOLDER = AVATAR_UPLOAD_ROOT / "avatars"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
LEGACY_AVATAR_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def process_avatar_image(file_stream) -> dict:
    """压缩+中心裁剪+缩略图，统一输出JPEG bytes。"""
    img = Image.open(file_stream)

    # 转换为RGB模式（处理RGBA等）
    if img.mode != "RGB":
        img = img.convert("RGB")

    original_width, original_height = img.size

    # 裁剪为正方形（中心裁剪）
    min_side = min(original_width, original_height)
    left = (original_width - min_side) // 2
    top = (original_height - min_side) // 2
    right = left + min_side
    bottom = top + min_side
    img = img.crop((left, top, right, bottom))

    img = img.resize(AVATAR_MAX_SIZE, Image.LANCZOS)
    thumbnail = img.resize(AVATAR_THUMBNAIL_SIZE, Image.LANCZOS)

    main_buffer = io.BytesIO()
    img.save(main_buffer, format="JPEG", quality=85, optimize=True)
    main_buffer.seek(0)

    thumb_buffer = io.BytesIO()
    thumbnail.save(thumb_buffer, format="JPEG", quality=80, optimize=True)
    thumb_buffer.seek(0)

    main_size = len(main_buffer.getvalue())

    return {
        "main_image": main_buffer,
        "thumbnail": thumb_buffer,
        "width": AVATAR_MAX_SIZE[0],
        "height": AVATAR_MAX_SIZE[1],
        "file_size": main_size,
        "format": "jpg",
    }


def _build_avatar_url(filename: str) -> str:
    return f"/api/user/uploads/avatars/{filename}"


def _resolve_avatar_file(filename: str) -> Path | None:
    if not filename:
        return None

    safe_name = Path(filename).name
    for candidate in (UPLOAD_FOLDER / safe_name, LEGACY_AVATAR_FOLDER / safe_name):
        if candidate.is_file():
            return candidate
    return None


def _extract_user_id_from_auth_header() -> int | None:
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header:
        return None
    token = auth_header
    if token.startswith("Bearer "):
        token = token[7:]
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("user_id")


def _fetchone_compat(cursor, statements, params=()):
    """Try compatible SELECT variants for environments with older schemas."""
    last_error = None
    for statement in statements:
        try:
            cursor.execute(statement, params)
            return cursor.fetchone()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error:
        raise last_error
    return None


def _fetchall_compat(cursor, statements, params=(), row_defaults=None):
    """Try compatible SELECT variants for environments with older schemas."""
    last_error = None
    for statement in statements:
        try:
            cursor.execute(statement, params)
            rows = cursor.fetchall() or []
            if row_defaults:
                return [{**row_defaults, **row} for row in rows]
            return rows
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error:
        raise last_error
    return []


@user_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """获取用户资料（供个人资料页面初始化）"""
    user_id = request.user_id
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 尝试完整字段查询（包含检修岗位信息字段）
            for stmt in [
                """
                SELECT id, phone, name, avatar, gender, age, height, weight, bio,
                       level, level_name, department, position, specialty,
                       skill_level, certifications, employee_id
                FROM users WHERE id = %s AND status = 'active'
                """,
                """
                SELECT id, phone, name, avatar, gender, age, height, weight, bio, level, level_name
                FROM users WHERE id = %s AND status = 'active'
                """,
                """
                SELECT id, phone, name, avatar, level, level_name
                FROM users WHERE id = %s AND status = 'active'
                """,
            ]:
                try:
                    cursor.execute(stmt, (user_id,))
                    user = cursor.fetchone()
                    break
                except Exception:
                    user = None
            if not user:
                return error_response(404, "用户不存在")

            # 补齐可能缺失的字段
            for field in ["gender", "age", "height", "weight", "bio", "department", "position",
                          "specialty", "skill_level", "certifications", "employee_id"]:
                user.setdefault(field, None)

            # work_years 映射：优先用 work_years 列，回退到 height 列
            user["work_years"] = user.get("work_years") or user.get("height")

            cursor.execute(
                """
                SELECT theme, language, notifications_enabled, privacy_level
                FROM user_settings
                WHERE user_id = %s
                """,
                (user_id,),
            )
            settings = cursor.fetchone() or {}

        return success_response({"user": user, "settings": settings}, "获取用户资料成功")
    except Exception as e:
        logger.exception("获取用户资料失败")
        return error_response(500, f"获取失败：{str(e)}")


@user_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    """更新用户资料（个人资料编辑页保存）"""
    user_id = request.user_id
    try:
        data = request.get_json(silent=True) or {}
        if not data:
            return error_response(400, "请求数据格式错误")

        allowed_fields = ["name", "gender", "age", "height", "weight", "bio", "avatar",
                           "department", "position", "specialty", "skill_level",
                           "certifications", "employee_id", "work_years"]
        update_fields = []
        update_values = []

        # name
        if "name" in data:
            name = (data.get("name") or "").strip()
            if len(name) < 2:
                return error_response(400, "用户名长度不能少于2位")
            update_fields.append("name = %s")
            update_values.append(name)

        # gender
        if "gender" in data:
            gender = (data.get("gender") or "").strip()
            if gender not in {"男", "女", "其他", ""}:
                return error_response(400, "性别格式不正确")
            update_fields.append("gender = %s")
            update_values.append(gender or None)

        # age
        if "age" in data and data.get("age") not in ("", None):
            age = int(data.get("age"))
            if age < 1 or age > 120:
                return error_response(400, "请输入有效年龄")
            update_fields.append("age = %s")
            update_values.append(age)

        # height / weight（向后兼容，height 存储工龄）
        if "height" in data and data.get("height") not in ("", None):
            height = float(data.get("height"))
            update_fields.append("height = %s")
            update_values.append(height)

        if "weight" in data and data.get("weight") not in ("", None):
            weight = float(data.get("weight"))
            update_fields.append("weight = %s")
            update_values.append(weight)

        # work_years（映射到 height 列，保持兼容）
        if "work_years" in data and data.get("work_years") not in ("", None):
            work_years = float(data.get("work_years"))
            update_fields.append("height = %s")
            update_values.append(work_years)

        # bio
        if "bio" in data:
            bio = (data.get("bio") or "").strip()
            update_fields.append("bio = %s")
            update_values.append(bio or None)

        # avatar
        if "avatar" in data:
            avatar = (data.get("avatar") or "").strip()
            if avatar:
                update_fields.append("avatar = %s")
                update_values.append(avatar)

        # 检修岗位信息字段（新字段，可能列不存在时跳过）
        text_fields = {
            "department": "department",
            "position": "position",
            "specialty": "specialty",
            "skill_level": "skill_level",
            "certifications": "certifications",
            "employee_id": "employee_id",
        }
        for api_field, db_col in text_fields.items():
            if api_field in data:
                val = (data.get(api_field) or "").strip()
                update_fields.append(f"{db_col} = %s")
                update_values.append(val or None)

        if not update_fields:
            return error_response(400, "没有需要更新的字段")

        update_values.append(user_id)
        sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, tuple(update_values))
            except Exception:
                # 新字段列可能不存在，回退到只更新基础字段
                basic_fields = []
                basic_values = []
                basic_names = {"name", "gender", "age", "height", "weight", "bio", "avatar"}
                for i, field_clause in enumerate(update_fields):
                    col_name = field_clause.split("=")[0].strip()
                    if col_name in basic_names:
                        basic_fields.append(field_clause)
                        basic_values.append(update_values[i])
                if basic_fields:
                    basic_values.append(user_id)
                    fallback_sql = f"UPDATE users SET {', '.join(basic_fields)} WHERE id = %s"
                    cursor.execute(fallback_sql, tuple(basic_values))
                else:
                    raise

            # 记录用户活动（用于个性化/审计，失败不阻塞）
            try:
                cursor.execute(
                    """
                    INSERT INTO user_activities (user_id, activity_type, activity_data, ip_address)
                    VALUES (%s, 'profile_update', %s, %s)
                    """,
                    (user_id, json.dumps({"fields": list(data.keys())}), request.remote_addr or ""),
                )
            except Exception:
                pass

            conn.commit()

        return success_response(None, "更新用户资料成功")
    except Exception as e:
        logger.exception("更新用户资料失败")
        return error_response(500, f"更新失败：{str(e)}")


@user_bp.route("/preferences", methods=["GET"])
@token_required
def get_preferences():
    """获取用户饮食偏好（用于个性化推荐/聊天）"""
    user_id = request.user_id
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT allergies, favorite_cuisines, dietary_habits, custom_notes, cooking_exp
                FROM user_preferences
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone() or {}

        # 前端页面当前直接把 res.data.data 赋值给 this.preferences
        # 因此这里保持扁平结构返回，避免接口不匹配导致偏好加载失败。
        return success_response(
            {
                "allergies": row.get("allergies") or "",
                "favorite_cuisines": row.get("favorite_cuisines") or "",
                "dietary_habits": row.get("dietary_habits") or "",
                "custom_notes": row.get("custom_notes") or "",
                "cooking_exp": row.get("cooking_exp") or 0,
            },
            "获取偏好成功",
        )
    except Exception as e:
        logger.exception("获取偏好失败")
        return error_response(500, f"获取偏好失败：{str(e)}")


@user_bp.route("/preferences", methods=["POST", "PUT"])
@token_required
def update_preferences():
    """更新用户饮食偏好（支持upsert）"""
    user_id = request.user_id
    try:
        data = request.get_json(silent=True) or {}

        def _to_text(v):
            if v is None:
                return None
            if isinstance(v, (dict, list)):
                return json.dumps(v, ensure_ascii=False)
            return str(v)

        allergies = _to_text(data.get("allergies"))
        favorite_cuisines = _to_text(data.get("favorite_cuisines"))
        dietary_habits = _to_text(data.get("dietary_habits"))
        custom_notes = _to_text(data.get("custom_notes"))
        cooking_exp = data.get("cooking_exp", 0)
        try:
            cooking_exp = int(cooking_exp)
        except Exception:
            cooking_exp = 0

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_preferences
                    (user_id, allergies, favorite_cuisines, dietary_habits, custom_notes, cooking_exp)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    allergies = VALUES(allergies),
                    favorite_cuisines = VALUES(favorite_cuisines),
                    dietary_habits = VALUES(dietary_habits),
                    custom_notes = VALUES(custom_notes),
                    cooking_exp = VALUES(cooking_exp)
                """,
                (user_id, allergies, favorite_cuisines, dietary_habits, custom_notes, cooking_exp),
            )

            # 偏好变更写入活动日志（不阻塞主流程）
            try:
                cursor.execute(
                    """
                    INSERT INTO user_activities (user_id, activity_type, activity_data, ip_address)
                    VALUES (%s, 'preferences_update', %s, %s)
                    """,
                    (user_id, json.dumps({"updated": list(data.keys())}, ensure_ascii=False), request.remote_addr or ""),
                )
            except Exception:
                pass

            conn.commit()

        return success_response(None, "更新偏好成功")
    except Exception as e:
        logger.exception("更新偏好失败")
        return error_response(500, f"更新偏好失败：{str(e)}")


@user_bp.route("/avatar", methods=["POST"])
@token_required
def upload_avatar():
    """上传用户头像（个人资料编辑页）"""
    user_id = request.user_id
    try:
        if "avatar" not in request.files:
            return error_response(400, "没有上传文件")

        file = request.files["avatar"]
        if not file or not file.filename:
            return error_response(400, "没有选择文件")

        if not allowed_file(file.filename):
            return error_response(400, "不支持的文件格式")

        # 文件大小校验（部分客户端不会提供准确content_length时，这里尽力处理）
        try:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            if file_size > MAX_FILE_SIZE:
                return error_response(400, "文件大小超过5MB限制")
        except Exception:
            file_size = None

        processed = process_avatar_image(file.stream)

        filename = f"{uuid.uuid4()}.jpg"
        thumbnail_filename = f"{uuid.uuid4()}_thumb.jpg"

        main_path = UPLOAD_FOLDER / filename
        thumb_path = UPLOAD_FOLDER / thumbnail_filename

        with open(main_path, "wb") as f:
            f.write(processed["main_image"].getvalue())
        with open(thumb_path, "wb") as f:
            f.write(processed["thumbnail"].getvalue())

        avatar_url = _build_avatar_url(filename)
        thumbnail_url = _build_avatar_url(thumbnail_filename)

        # 更新DB（user_avatars 表可能在某些数据库中不存在，因此写入做容错）
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 更新users.avatar
            cursor.execute("UPDATE users SET avatar = %s WHERE id = %s", (avatar_url, user_id))
            # 先提交用户头像主更新：后续 user_avatars 表如果不存在/写入失败，不应回滚用户头像改动
            conn.commit()

            try:
                cursor.execute(
                    """
                    UPDATE user_avatars
                    SET is_current = 0
                    WHERE user_id = %s AND is_current = 1
                    """,
                    (user_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO user_avatars
                    (user_id, avatar_url, thumbnail_url, file_size, file_format, width, height, is_current)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (
                        user_id,
                        avatar_url,
                        thumbnail_url,
                        processed["file_size"],
                        processed["format"],
                        processed["width"],
                        processed["height"],
                    ),
                )
            except Exception:
                # 不阻塞头像上传主流程（user_avatars 表可能不存在）
                try:
                    conn.rollback()
                except Exception:
                    pass

            try:
                cursor.execute(
                    """
                    INSERT INTO user_activities (user_id, activity_type, activity_data, ip_address)
                    VALUES (%s, 'avatar_upload', %s, %s)
                    """,
                    (user_id, json.dumps({"avatar_url": avatar_url}), request.remote_addr or ""),
                )
            except Exception:
                pass

            conn.commit()

        return success_response(
            {
                "avatar": avatar_url,
                "thumbnail": thumbnail_url,
                "width": processed["width"],
                "height": processed["height"],
                "file_size": processed["file_size"],
            },
            "头像上传成功",
        )
    except Exception as e:
        logger.exception("上传头像异常")
        return error_response(500, f"服务器内部错误：{str(e)}")


@user_bp.route("/uploads/avatars/<path:filename>", methods=["GET"])
def serve_avatar(filename):
    avatar_path = _resolve_avatar_file(filename)
    if not avatar_path:
        abort(404)
    return send_from_directory(str(avatar_path.parent), avatar_path.name, as_attachment=False, max_age=86400)


@user_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    """
    个人中心仪表盘数据（登录用户 or 游客均可调用）
    前端：登录态使用 Authorization Bearer token；游客态使用 X-Guest-Session。
    """
    try:
        user_id = _extract_user_id_from_auth_header()
        if not user_id:
            # 游客：返回默认个性化外观数据（不阻塞页面）
            return success_response(
                {
                    "profile": {
                        "id": None,
                        "name": None,
                        "avatar": None,
                        "level": 1,
                        "level_name": "新手",
                        "gender": None,
                        "age": None,
                        "height": None,
                        "weight": None,
                        "bio": None,
                    },
                    "panorama": {
                        "dimensions": {
                            "nutrition": 60,
                            "diversity": 55,
                            "sleep": 62,
                            "exercise": 58,
                            "environment": 57,
                        },
                        "trend": 0,
                    },
                    "maintenancePlan": {"name": "发动机检修技能提升计划", "daysCompleted": 0, "totalDays": 7, "completionRate": 0},
                    "skillDetail": {"safety_score": 85, "quality_score": 78, "efficiency_score": 72, "compliance_score": 80},
                    "achievements": [],
                    "recent_activities": [],
                    "stats": {
                        "total_analysis": 0,
                        "health_records_count": 0,
                        "takeaway_analysis_count": 0,
                        "favorites_count": 0,
                        "browse_history_count": 0,
                        "completed_goals": 0,
                    },
                },
                "获取仪表盘数据成功",
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()

            for stmt in [
                """
                SELECT id, phone, name, avatar, gender, age, height, weight, bio,
                       level, level_name, department, position, specialty,
                       skill_level, certifications, employee_id
                FROM users WHERE id = %s AND status = 'active'
                """,
                """
                SELECT id, phone, name, avatar, gender, age, height, weight, bio, level, level_name
                FROM users WHERE id = %s AND status = 'active'
                """,
                """
                SELECT id, phone, name, avatar, level, level_name
                FROM users WHERE id = %s AND status = 'active'
                """,
            ]:
                try:
                    cursor.execute(stmt, (user_id,))
                    profile = cursor.fetchone()
                    break
                except Exception:
                    profile = None
            if profile:
                for field in ["gender", "age", "height", "weight", "bio", "department",
                              "position", "specialty", "skill_level", "certifications", "employee_id"]:
                    profile.setdefault(field, None)
                profile["work_years"] = profile.get("work_years") or profile.get("height")
            if not profile:
                return error_response(404, "用户不存在")

            # goals
            try:
                cursor.execute(
                    """
                    SELECT calorie_goal, protein_goal, fat_goal, carbs_goal, steps_goal, water_goal
                    FROM health_goals
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                goals = cursor.fetchone() or {}
            except Exception:
                goals = {}
            calorie_goal = int(goals.get("calorie_goal") or 2000)
            protein_goal = float(goals.get("protein_goal") or 120)
            fat_goal = float(goals.get("fat_goal") or 60)
            carbs_goal = float(goals.get("carbs_goal") or 250)
            steps_goal = int(goals.get("steps_goal") or 10000)
            water_goal = int(goals.get("water_goal") or 2000)

            # preferences
            prefs = _fetchone_compat(
                cursor,
                [
                    """
                    SELECT allergies, favorite_cuisines, dietary_habits, custom_notes, cooking_exp
                    FROM user_preferences
                    WHERE user_id = %s
                    """,
                    """
                    SELECT allergies, favorite_cuisines, dietary_habits, custom_notes
                    FROM user_preferences
                    WHERE user_id = %s
                    """,
                ],
                (user_id,),
            ) or {}
            dietary_habits = (prefs.get("dietary_habits") or "") or ""

            # health_records last 14 days for panorama/trend
            records = _fetchall_compat(
                cursor,
                [
                    """
                    SELECT record_date, calories, protein, fat, carbs, steps, water, sleep_hours
                    FROM health_records
                    WHERE user_id = %s AND record_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                    ORDER BY record_date DESC
                    """,
                    """
                    SELECT record_date, calories, protein, fat, carbs, steps, water
                    FROM health_records
                    WHERE user_id = %s AND record_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                    ORDER BY record_date DESC
                    """,
                ],
                (user_id,),
                row_defaults={"sleep_hours": 0},
            )

            def _clamp(v: float, lo: float, hi: float) -> float:
                return max(lo, min(hi, v))

            # 聚合近7/前7日
            today = datetime.utcnow().date()
            last7_start = today - timedelta(days=6)
            prev7_start = today - timedelta(days=13)
            prev7_end = today - timedelta(days=7)

            def _in_range(d, start_d, end_d):
                return start_d <= d <= end_d

            current_days = []
            prev_days = []
            for r in records:
                # MySQL Date 可能直接是 date，也可能是 str
                d = r["record_date"]
                if isinstance(d, str):
                    d = datetime.strptime(d, "%Y-%m-%d").date()
                if _in_range(d, last7_start, today):
                    current_days.append(r)
                elif _in_range(d, prev7_start, prev7_end):
                    prev_days.append(r)

            def _avg(key: str, arr):
                vals = [float(x.get(key) or 0) for x in arr]
                return (sum(vals) / len(vals)) if vals else 0.0

            avg_calories = _avg("calories", current_days)
            avg_protein = _avg("protein", current_days)
            avg_fat = _avg("fat", current_days)
            avg_carbs = _avg("carbs", current_days)
            avg_steps = _avg("steps", current_days)
            avg_water = _avg("water", current_days)
            avg_sleep = _avg("sleep_hours", current_days)

            # dimensions
            nutrition = 50.0
            if protein_goal > 0 and calorie_goal > 0:
                protein_ratio = avg_protein / protein_goal
                calories_ratio = avg_calories / calorie_goal if calorie_goal else 1
                carbs_ratio = (avg_carbs / carbs_goal) if carbs_goal else 1
                fat_ratio = (avg_fat / fat_goal) if fat_goal else 1
                # 越接近1分越高；简单启发式
                nutrition = (
                    100
                    - (abs(protein_ratio - 1) * 35 + abs(calories_ratio - 1) * 25 + abs(carbs_ratio - 1) * 15 + abs(fat_ratio - 1) * 15)
                )
                nutrition = _clamp(nutrition, 0, 100)

            diversity = 55.0
            try:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS c
                    FROM favorites
                    WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    """,
                    (user_id,),
                )
                fav_row = cursor.fetchone() or {}
                fav_count = int(fav_row.get("c") or 0)
                diversity = _clamp(40 + fav_count * 5, 0, 100)
            except Exception:
                pass

            sleep_score = 50.0
            if avg_sleep > 0:
                sleep_score = _clamp((avg_sleep / 8.0) * 100, 0, 100)

            exercise = 50.0
            if steps_goal > 0:
                exercise = _clamp((avg_steps / float(steps_goal)) * 100, 0, 100)

            environment = 50.0
            if water_goal > 0:
                environment = _clamp((avg_water / float(water_goal)) * 100, 0, 100)
            if "低碳" in dietary_habits or "减脂" in dietary_habits:
                environment = _clamp(environment + 8, 0, 100)

            # trend
            avg_prev_calories = _avg("calories", prev_days)
            if avg_prev_calories > 0:
                trend = int(((avg_calories - avg_prev_calories) / avg_prev_calories) * 100)
                trend = int(_clamp(trend, -100, 100))
            else:
                trend = 0

            panorama = {
                "dimensions": {
                    "nutrition": int(nutrition),
                    "diversity": int(diversity),
                    "sleep": int(sleep_score),
                    "exercise": int(exercise),
                    "environment": int(environment),
                },
                "trend": trend,
            }

            # skill detail
            skillDetail = {
                "safety_score": 85,
                "quality_score": 78,
                "efficiency_score": 72,
                "compliance_score": 80,
            }

            # maintenance plan
            days_completed = len({r["record_date"] for r in current_days}) if current_days else 0
            plan_name = "发动机检修技能提升计划"
            maintenancePlan = {"name": plan_name, "daysCompleted": days_completed, "totalDays": 7}

            # achievements
            try:
                cursor.execute("SELECT id, name, icon, description FROM achievements ORDER BY id ASC")
                all_ach = cursor.fetchall() or []
            except Exception:
                all_ach = []

            unlocked_rows = _fetchall_compat(
                cursor,
                [
                    """
                    SELECT achievement_id, unlocked_at
                    FROM user_achievements
                    WHERE user_id = %s
                    """,
                    """
                    SELECT achievement_id
                    FROM user_achievements
                    WHERE user_id = %s
                    """,
                ],
                (user_id,),
                row_defaults={"unlocked_at": None},
            )
            unlocked_map = {r["achievement_id"]: r.get("unlocked_at") for r in unlocked_rows}

            achievements = [
                {
                    "id": a["id"],
                    "name": a["name"],
                    "icon": a.get("icon"),
                    "description": a.get("description"),
                    "unlocked": a["id"] in unlocked_map,
                }
                for a in all_ach
            ]

            # recent activities
            try:
                cursor.execute(
                    """
                    SELECT activity_type, activity_data, created_at
                    FROM user_activities
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 5
                    """,
                    (user_id,),
                )
                recent_activities = cursor.fetchall() or []
            except Exception:
                recent_activities = []

            def _safe_count(table_name, time_field=None, interval_days=None):
                try:
                    sql = f"SELECT COUNT(*) AS c FROM {table_name} WHERE user_id = %s"
                    params = [user_id]
                    if time_field and interval_days:
                        sql += f" AND {time_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                        params.append(interval_days)
                    cursor.execute(sql, tuple(params))
                    row = cursor.fetchone() or {}
                    return int(row.get("c") or 0)
                except Exception:
                    return 0

            health_records_count = _safe_count("health_records")
            takeaway_analysis_count = _safe_count("takeaway_analysis")
            favorites_count = _safe_count("favorites")
            browse_history_count = _safe_count("browse_history", "visited_at", 30)
            stats = {
                "total_analysis": health_records_count + takeaway_analysis_count,
                "health_records_count": health_records_count,
                "takeaway_analysis_count": takeaway_analysis_count,
                "favorites_count": favorites_count,
                "browse_history_count": browse_history_count,
                "completed_goals": days_completed,
            }

        return success_response(
            {
                "profile": profile,
                "panorama": panorama,
                "maintenancePlan": {
                    **maintenancePlan,
                    "completionRate": int(round((days_completed / max(maintenancePlan["totalDays"], 1)) * 100)),
                },
                "skillDetail": skillDetail,
                "achievements": achievements,
                "recent_activities": recent_activities,
                "stats": stats,
            },
            "获取仪表盘数据成功",
        )
    except Exception as e:
        logger.exception("获取仪表盘数据失败")
        return error_response(500, f"获取仪表盘数据失败：{str(e)}")

