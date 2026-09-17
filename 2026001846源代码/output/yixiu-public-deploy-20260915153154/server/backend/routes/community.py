import json
import math
import os
import uuid
from pathlib import Path

from flask import Blueprint, abort, request, send_from_directory
from flask_cors import CORS

from utils import error_response, get_db_connection, success_response

community_bp = Blueprint("community", __name__)
CORS(community_bp)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_POST_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
POST_UPLOAD_ROOT = Path(
    os.getenv("COMMUNITY_UPLOAD_ROOT", str(PROJECT_ROOT / "uploads"))
).expanduser()
POST_IMAGE_FOLDER = POST_UPLOAD_ROOT / "community_posts"
POST_IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_image_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def build_post_image_url(filename: str) -> str:
    return f"/api/community/uploads/posts/{filename}"


def resolve_post_image_file(filename: str) -> Path | None:
    if not filename:
        return None
    candidate = POST_IMAGE_FOLDER / Path(filename).name
    if candidate.is_file():
        return candidate
    return None


def calculate_distance(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None

    radius_km = 6371
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(radius_km * c, 2)


def parse_json_field(value, default):
    if value in (None, "", []):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def compute_member_percentage(current_members, max_members):
    if not max_members:
        return 0
    return round((current_members or 0) * 100 / max_members, 1)


def normalize_post_row(post, is_liked=False):
    images = parse_json_field(post.get("images"), [])
    tags = parse_json_field(post.get("tags"), [])
    carbon_saved = None
    for tag in tags:
        if isinstance(tag, str) and tag.startswith("carbon:"):
            try:
                carbon_saved = int(tag.split(":", 1)[1])
            except (TypeError, ValueError):
                carbon_saved = None
            break

    payload = {
        "id": post["id"],
        "community_id": post.get("community_id"),
        "community_name": post.get("community_name"),
        "title": post.get("title"),
        "content": post.get("content"),
        "images": images,
        "category": post.get("category") or "general",
        "tags": tags,
        "author": {
            "id": post.get("user_id"),
            "name": post.get("author_name") or "用户",
            "avatar": post.get("author_avatar"),
        },
        "likes": post.get("like_count") or 0,
        "comments": post.get("comment_count") or 0,
        "shares": post.get("share_count") or 0,
        "is_liked": is_liked,
        "isLiked": is_liked,
        "createdAt": post.get("created_at").isoformat() if post.get("created_at") else None,
        "created_at": post.get("created_at").isoformat() if post.get("created_at") else None,
    }
    if carbon_saved:
        payload["carbonSaved"] = carbon_saved
        payload["carbonPoints"] = math.ceil(carbon_saved / 100)
    return payload


def get_home_feed_community_id(cursor):
    cursor.execute(
        """
        SELECT id
        FROM communities
        WHERE status = 'active' AND is_public = 1
        ORDER BY id ASC
        LIMIT 1
        """
    )
    community = cursor.fetchone()
    return community["id"] if community else None


def resolve_home_feed_user_id(cursor, user_id):
    if user_id:
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return user["id"]

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE status = 'active'
        ORDER BY id ASC
        LIMIT 1
        """
    )
    user = cursor.fetchone()
    return user["id"] if user else None


def get_joined_community_ids(user_id):
    if not user_id:
        return set()

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT community_id
                FROM community_members
                WHERE user_id = %s AND status = 'active'
                """,
                (user_id,),
            )
            return {row["community_id"] for row in cursor.fetchall()}


@community_bp.route("/nearby", methods=["GET"])
def get_nearby_communities():
    user_id = request.args.get("user_id", type=int)
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    radius = request.args.get("radius", default=10.0, type=float)
    sort_by = request.args.get("sort_by", default="distance", type=str)
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)

    if lat is None or lon is None:
        return error_response(400, "缺少位置参数")

    joined = get_joined_community_ids(user_id)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, description, avatar, cover_image, category,
                       latitude, longitude, address, max_members, current_members,
                       post_count, activity_score, join_type, tags, created_at
                FROM communities
                WHERE is_public = 1 AND status = 'active'
                """
            )
            communities = cursor.fetchall()

    result = []
    for community in communities:
        distance = calculate_distance(lat, lon, community.get("latitude"), community.get("longitude"))
        if distance is None or distance > radius:
            continue

        community["distance"] = distance
        community["is_joined"] = community["id"] in joined
        community["member_percentage"] = compute_member_percentage(
            community.get("current_members"), community.get("max_members")
        )
        community["tags"] = parse_json_field(community.get("tags"), [])
        result.append(community)

    if sort_by == "members":
        result.sort(key=lambda item: item.get("current_members", 0), reverse=True)
    elif sort_by == "activity":
        result.sort(key=lambda item: float(item.get("activity_score") or 0), reverse=True)
    else:
        result.sort(key=lambda item: item.get("distance", 0))

    total = len(result)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return success_response(
        {
            "communities": result[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        },
        "获取成功",
    )


@community_bp.route("/search", methods=["GET"])
def search_communities():
    keyword = request.args.get("keyword", default="", type=str)
    category = request.args.get("category", type=str)
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=20, type=int)

    conditions = ["is_public = 1", "status = 'active'"]
    params = []

    if keyword:
        conditions.append("(name LIKE %s OR description LIKE %s)")
        like = f"%{keyword}%"
        params.extend([like, like])

    if category:
        conditions.append("category = %s")
        params.append(category)

    where_clause = " AND ".join(conditions)
    offset = max(0, (page - 1) * page_size)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total FROM communities WHERE {where_clause}", params)
            total = cursor.fetchone()["total"]
            cursor.execute(
                f"""
                SELECT id, name, description, avatar, cover_image, category,
                       latitude, longitude, address, max_members, current_members,
                       post_count, activity_score, join_type, tags, created_at
                FROM communities
                WHERE {where_clause}
                ORDER BY activity_score DESC, created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [page_size, offset],
            )
            communities = cursor.fetchall()

    for community in communities:
        community["tags"] = parse_json_field(community.get("tags"), [])
        community["member_percentage"] = compute_member_percentage(
            community.get("current_members"), community.get("max_members")
        )

    return success_response(
        {
            "communities": communities,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        },
        "搜索成功",
    )


@community_bp.route("/<int:community_id>", methods=["GET"])
def get_community_detail(community_id):
    user_id = request.args.get("user_id", type=int)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.*, u.name AS creator_name, u.avatar AS creator_avatar
                FROM communities c
                LEFT JOIN users u ON c.creator_id = u.id
                WHERE c.id = %s
                """,
                (community_id,),
            )
            community = cursor.fetchone()
            if not community:
                return error_response(404, "社区不存在")

            is_joined = False
            user_role = None
            if user_id:
                cursor.execute(
                    """
                    SELECT role
                    FROM community_members
                    WHERE community_id = %s AND user_id = %s AND status = 'active'
                    """,
                    (community_id, user_id),
                )
                member = cursor.fetchone()
                if member:
                    is_joined = True
                    user_role = member["role"]

            cursor.execute(
                """
                SELECT cm.role, u.name, u.avatar
                FROM community_members cm
                JOIN users u ON cm.user_id = u.id
                WHERE cm.community_id = %s
                  AND cm.status = 'active'
                  AND cm.role IN ('owner', 'admin', 'moderator')
                ORDER BY FIELD(cm.role, 'owner', 'admin', 'moderator')
                """,
                (community_id,),
            )
            admins = cursor.fetchall()

    community["tags"] = parse_json_field(community.get("tags"), [])
    community["is_joined"] = is_joined
    community["user_role"] = user_role
    community["admins"] = admins
    community["member_percentage"] = compute_member_percentage(
        community.get("current_members"), community.get("max_members")
    )
    return success_response(community, "获取成功")


@community_bp.route("/<int:community_id>/join", methods=["POST"])
def join_community(community_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    message = data.get("message", "")

    if not user_id:
        return error_response(400, "缺少用户ID")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, join_type, current_members, max_members
                FROM communities
                WHERE id = %s
                """,
                (community_id,),
            )
            community = cursor.fetchone()
            if not community:
                return error_response(404, "社区不存在")

            cursor.execute(
                """
                SELECT id, status
                FROM community_members
                WHERE community_id = %s AND user_id = %s
                """,
                (community_id, user_id),
            )
            member = cursor.fetchone()
            if member and member["status"] == "active":
                return error_response(400, "您已经是该社区成员")

            if (community.get("current_members") or 0) >= (community.get("max_members") or 0):
                return error_response(400, "社区成员已满")

            if community["join_type"] == "open":
                if member:
                    cursor.execute(
                        """
                        UPDATE community_members
                        SET status = 'active', role = 'member', join_date = NOW()
                        WHERE id = %s
                        """,
                        (member["id"],),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO community_members (community_id, user_id, role, status)
                        VALUES (%s, %s, 'member', 'active')
                        """,
                        (community_id, user_id),
                    )

                cursor.execute(
                    """
                    UPDATE communities
                    SET current_members = current_members + 1
                    WHERE id = %s
                    """,
                    (community_id,),
                )
                conn.commit()
                return success_response({"status": "approved"}, "加入成功")

            cursor.execute(
                """
                SELECT id
                FROM community_join_requests
                WHERE community_id = %s AND user_id = %s AND status = 'pending'
                """,
                (community_id, user_id),
            )
            pending = cursor.fetchone()
            if pending:
                return error_response(400, "您已有待审核的加入申请")

            cursor.execute(
                """
                INSERT INTO community_join_requests (community_id, user_id, message, status)
                VALUES (%s, %s, %s, 'pending')
                """,
                (community_id, user_id, message),
            )
            conn.commit()
            return success_response({"status": "pending"}, "申请已提交，等待审核")


@community_bp.route("/posts/feed", methods=["GET"])
def get_home_post_feed():
    user_id = request.args.get("user_id", type=int)
    category = request.args.get("category", type=str)
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)
    offset = max(0, (page - 1) * page_size)

    conditions = ["p.status = 'published'", "c.status = 'active'", "c.is_public = 1"]
    params = []
    if category and category != "all":
        conditions.append("p.category = %s")
        params.append(category)
    where_clause = " AND ".join(conditions)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM community_posts p
                JOIN communities c ON p.community_id = c.id
                WHERE {where_clause}
                """,
                params,
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    p.*,
                    c.name AS community_name,
                    u.name AS author_name,
                    u.avatar AS author_avatar
                FROM community_posts p
                JOIN communities c ON p.community_id = c.id
                JOIN users u ON p.user_id = u.id
                WHERE {where_clause}
                ORDER BY p.is_pinned DESC, p.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [page_size, offset],
            )
            posts = cursor.fetchall()

            liked_post_ids = set()
            if user_id and posts:
                cursor.execute(
                    f"""
                    SELECT post_id
                    FROM community_post_likes
                    WHERE user_id = %s AND post_id IN ({','.join(['%s'] * len(posts))})
                    """,
                    [user_id] + [post["id"] for post in posts],
                )
                liked_post_ids = {row["post_id"] for row in cursor.fetchall()}

    return success_response(
        {
            "posts": [normalize_post_row(post, post["id"] in liked_post_ids) for post in posts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        },
        "获取成功",
    )


@community_bp.route("/posts/feed", methods=["POST"])
def create_home_post():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    content = (data.get("content") or "").strip()

    if not content:
        return error_response(400, "缺少必要参数")

    title = data.get("title")
    images = data.get("images") or []
    category = data.get("category", "general")
    tags = data.get("tags") or []

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            community_id = data.get("community_id") or get_home_feed_community_id(cursor)
            if not community_id:
                return error_response(404, "社区不存在")

            user_id = resolve_home_feed_user_id(cursor, user_id)
            if not user_id:
                return error_response(404, "用户不存在")

            cursor.execute(
                """
                INSERT INTO community_posts
                (community_id, user_id, title, content, images, category, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    community_id,
                    user_id,
                    title,
                    content,
                    json.dumps(images, ensure_ascii=False) if images else None,
                    category,
                    json.dumps(tags, ensure_ascii=False) if tags else None,
                ),
            )
            post_id = cursor.lastrowid
            cursor.execute(
                """
                UPDATE communities
                SET post_count = post_count + 1
                WHERE id = %s
                """,
                (community_id,),
            )
            conn.commit()

    return success_response({"post_id": post_id}, "发布成功")


@community_bp.route("/<int:community_id>/posts", methods=["GET"])
def get_community_posts(community_id):
    user_id = request.args.get("user_id", type=int)
    category = request.args.get("category", type=str)
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)
    offset = max(0, (page - 1) * page_size)

    conditions = ["p.community_id = %s", "p.status = 'published'"]
    params = [community_id]
    if category:
        conditions.append("p.category = %s")
        params.append(category)
    where_clause = " AND ".join(conditions)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total FROM community_posts p WHERE {where_clause}", params)
            total = cursor.fetchone()["total"]
            cursor.execute(
                f"""
                SELECT p.*, u.name AS author_name, u.avatar AS author_avatar
                FROM community_posts p
                JOIN users u ON p.user_id = u.id
                WHERE {where_clause}
                ORDER BY p.is_pinned DESC, p.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [page_size, offset],
            )
            posts = cursor.fetchall()

            for post in posts:
                post["images"] = parse_json_field(post.get("images"), [])
                if user_id:
                    cursor.execute(
                        """
                        SELECT id
                        FROM community_post_likes
                        WHERE post_id = %s AND user_id = %s
                        """,
                        (post["id"], user_id),
                    )
                    post["is_liked"] = cursor.fetchone() is not None
                else:
                    post["is_liked"] = False

    return success_response(
        {
            "posts": posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        },
        "获取成功",
    )


@community_bp.route("/<int:community_id>/posts", methods=["POST"])
def create_post(community_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    content = data.get("content")

    if not user_id or not content:
        return error_response(400, "缺少必要参数")

    title = data.get("title")
    images = data.get("images") or []
    category = data.get("category", "general")
    tags = data.get("tags") or []

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM community_members
                WHERE community_id = %s AND user_id = %s AND status = 'active'
                """,
                (community_id, user_id),
            )
            if not cursor.fetchone():
                return error_response(403, "您不是该社区成员")

            cursor.execute(
                """
                INSERT INTO community_posts
                (community_id, user_id, title, content, images, category, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    community_id,
                    user_id,
                    title,
                    content,
                    json.dumps(images, ensure_ascii=False) if images else None,
                    category,
                    json.dumps(tags, ensure_ascii=False) if tags else None,
                ),
            )
            post_id = cursor.lastrowid
            cursor.execute(
                """
                UPDATE communities
                SET post_count = post_count + 1
                WHERE id = %s
                """,
                (community_id,),
            )
            conn.commit()

    return success_response({"post_id": post_id}, "发布成功")


@community_bp.route("/upload-image", methods=["POST"])
@community_bp.route("/posts/upload-image", methods=["POST"])
def upload_post_image():
    user_id = getattr(request, "user_id", None) or request.form.get("user_id", type=int) or 0
    if "image" not in request.files:
        return error_response(400, "娌℃湁涓婁紶鍥剧墖")

    file = request.files["image"]
    if not file or not file.filename:
        return error_response(400, "娌℃湁閫夋嫨鍥剧墖")

    if not allowed_image_file(file.filename):
        return error_response(400, "涓嶆敮鎸佺殑鍥剧墖鏍煎紡")

    try:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_POST_IMAGE_SIZE:
            return error_response(400, "鍥剧墖澶у皬瓒呰繃10MB闄愬埗")
    except Exception:
        file_size = None

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{user_id}_{uuid.uuid4().hex}.{ext}"
    save_path = POST_IMAGE_FOLDER / filename
    file.save(save_path)

    return success_response(
        {
            "url": build_post_image_url(filename),
            "filename": filename,
            "file_size": file_size,
        },
        "涓婁紶鎴愬姛",
    )


@community_bp.route("/uploads/posts/<path:filename>", methods=["GET"])
def serve_post_image(filename):
    image_path = resolve_post_image_file(filename)
    if not image_path:
        abort(404)
    return send_from_directory(str(image_path.parent), image_path.name, as_attachment=False, max_age=86400)


@community_bp.route("/posts/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return error_response(400, "缺少用户ID")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM community_post_likes
                WHERE post_id = %s AND user_id = %s
                """,
                (post_id, user_id),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "DELETE FROM community_post_likes WHERE id = %s",
                    (existing["id"],),
                )
                cursor.execute(
                    """
                    UPDATE community_posts
                    SET like_count = GREATEST(like_count - 1, 0)
                    WHERE id = %s
                    """,
                    (post_id,),
                )
                conn.commit()
                return success_response({"is_liked": False}, "取消点赞")

            cursor.execute(
                """
                INSERT INTO community_post_likes (post_id, user_id)
                VALUES (%s, %s)
                """,
                (post_id, user_id),
            )
            cursor.execute(
                """
                UPDATE community_posts
                SET like_count = like_count + 1
                WHERE id = %s
                """,
                (post_id,),
            )
            conn.commit()
            return success_response({"is_liked": True}, "点赞成功")


@community_bp.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id") or request.args.get("user_id", type=int)
    if not user_id:
        return error_response(400, "缺少用户ID")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, community_id, status
                FROM community_posts
                WHERE id = %s
                """,
                (post_id,),
            )
            post = cursor.fetchone()
            if not post or post.get("status") == "deleted":
                return error_response(404, "帖子不存在")

            if int(post["user_id"]) != int(user_id):
                return error_response(403, "只能删除自己发布的帖子")

            cursor.execute(
                """
                UPDATE community_posts
                SET status = 'deleted'
                WHERE id = %s
                """,
                (post_id,),
            )
            cursor.execute(
                """
                UPDATE communities
                SET post_count = GREATEST(post_count - 1, 0)
                WHERE id = %s
                """,
                (post["community_id"],),
            )
            conn.commit()

    return success_response({"post_id": post_id}, "删除成功")


@community_bp.route("/posts/<int:post_id>/comments", methods=["GET"])
def get_post_comments(post_id):
    user_id = request.args.get("user_id", type=int)
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=20, type=int)
    offset = max(0, (page - 1) * page_size)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM community_post_comments
                WHERE post_id = %s AND status = 'published'
                """,
                (post_id,),
            )
            total = cursor.fetchone()["total"]
            cursor.execute(
                """
                SELECT c.*, u.name AS author_name, u.avatar AS author_avatar
                FROM community_post_comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.post_id = %s AND c.status = 'published'
                ORDER BY c.created_at ASC
                LIMIT %s OFFSET %s
                """,
                (post_id, page_size, offset),
            )
            comments = cursor.fetchall()

            for comment in comments:
                comment["images"] = parse_json_field(comment.get("images"), [])
                if user_id:
                    cursor.execute(
                        """
                        SELECT id
                        FROM community_comment_likes
                        WHERE comment_id = %s AND user_id = %s
                        """,
                        (comment["id"], user_id),
                    )
                    comment["is_liked"] = cursor.fetchone() is not None
                else:
                    comment["is_liked"] = False

    return success_response(
        {
            "comments": comments,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        },
        "获取成功",
    )


@community_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
def create_comment(post_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    content = data.get("content")
    if not user_id or not content:
        return error_response(400, "缺少必要参数")

    parent_id = data.get("parent_id")
    images = data.get("images") or []

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT community_id
                FROM community_posts
                WHERE id = %s
                """,
                (post_id,),
            )
            post = cursor.fetchone()
            if not post:
                return error_response(404, "帖子不存在")

            cursor.execute(
                """
                SELECT id
                FROM community_members
                WHERE community_id = %s AND user_id = %s AND status = 'active'
                """,
                (post["community_id"], user_id),
            )
            if not cursor.fetchone():
                return error_response(403, "您不是该社区成员")

            cursor.execute(
                """
                INSERT INTO community_post_comments
                (post_id, user_id, parent_id, content, images)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    post_id,
                    user_id,
                    parent_id,
                    content,
                    json.dumps(images, ensure_ascii=False) if images else None,
                ),
            )
            comment_id = cursor.lastrowid
            cursor.execute(
                """
                UPDATE community_posts
                SET comment_count = comment_count + 1
                WHERE id = %s
                """,
                (post_id,),
            )
            if parent_id:
                cursor.execute(
                    """
                    UPDATE community_post_comments
                    SET reply_count = reply_count + 1
                    WHERE id = %s
                    """,
                    (parent_id,),
                )
            conn.commit()

    return success_response({"comment_id": comment_id}, "评论成功")


@community_bp.route("/comments/<int:comment_id>/like", methods=["POST"])
def like_comment(comment_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return error_response(400, "缺少用户ID")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM community_comment_likes
                WHERE comment_id = %s AND user_id = %s
                """,
                (comment_id, user_id),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute("DELETE FROM community_comment_likes WHERE id = %s", (existing["id"],))
                cursor.execute(
                    """
                    UPDATE community_post_comments
                    SET like_count = GREATEST(like_count - 1, 0)
                    WHERE id = %s
                    """,
                    (comment_id,),
                )
                conn.commit()
                return success_response({"is_liked": False}, "取消点赞")

            cursor.execute(
                """
                INSERT INTO community_comment_likes (comment_id, user_id)
                VALUES (%s, %s)
                """,
                (comment_id, user_id),
            )
            cursor.execute(
                """
                UPDATE community_post_comments
                SET like_count = like_count + 1
                WHERE id = %s
                """,
                (comment_id,),
            )
            conn.commit()
            return success_response({"is_liked": True}, "点赞成功")
