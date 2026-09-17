import logging
from flask import Blueprint, request, jsonify
from utils import get_db_connection, success_response, error_response, validate_required_fields, decode_token
from datetime import datetime, timedelta

recipe_recommendation_bp = Blueprint('recipe_recommendation', __name__)
logger = logging.getLogger(__name__)


@recipe_recommendation_bp.route('/lists', methods=['GET'])
def get_recommendation_lists():
    """获取所有推荐榜单"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, name, type, description, icon, sort_order
            FROM recommendation_lists
            WHERE is_active = 1
            ORDER BY sort_order ASC
        """)
        
        lists = cursor.fetchall()
        conn.close()
        
        return success_response(lists, '获取榜单列表成功')
        
    except Exception as e:
        logger.error(f"获取榜单列表失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/lists/<int:list_id>/recipes', methods=['GET'])
def get_list_recipes(list_id):
    """获取指定榜单的菜品列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        offset = (page - 1) * page_size
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT r.id, r.name, r.image, r.description, r.cuisine, 
                   r.cooking_time, r.difficulty, r.calories,
                   lr.rank_position, lr.score,
                   COALESCE(AVG(rr.rating), 0) as avg_rating,
                   COUNT(DISTINCT rl.id) as like_count,
                   COUNT(DISTINCT rc.id) as comment_count
            FROM list_recipes lr
            JOIN recipes r ON lr.recipe_id = r.id
            LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
            LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
            LEFT JOIN recipe_comments rc ON r.id = rc.recipe_id
            WHERE lr.list_id = ?
            GROUP BY r.id, lr.rank_position, lr.score
            ORDER BY lr.rank_position ASC
            LIMIT ? OFFSET ?
        """, (list_id, page_size, offset))
        
        recipes = cursor.fetchall()
        
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM list_recipes
            WHERE list_id = ?
        """, (list_id,))
        
        total = cursor.fetchone()['total']
        
        conn.close()
        
        return success_response({
            'recipes': recipes,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        }, '获取榜单菜品成功')
        
    except Exception as e:
        logger.error(f"获取榜单菜品失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/recipes/<int:recipe_id>/detail', methods=['GET'])
def get_recipe_detail(recipe_id):
    """获取菜品详情"""
    try:
        token = request.headers.get('Authorization')
        user_id = None
        if token and token.startswith('Bearer '):
            payload = decode_token(token[7:])
            if payload:
                user_id = payload['user_id']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT r.id, r.name, r.image, r.description, r.cuisine,
                   r.cooking_time, r.difficulty, r.calories,
                   r.ingredients, r.steps, r.tags, r.created_at,
                   COALESCE(AVG(rr.rating), 0) as avg_rating,
                   COUNT(DISTINCT rr.id) as rating_count,
                   COUNT(DISTINCT rl.id) as like_count,
                   COUNT(DISTINCT rc.id) as comment_count
            FROM recipes r
            LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
            LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
            LEFT JOIN recipe_comments rc ON r.id = rc.recipe_id
            WHERE r.id = ?
            GROUP BY r.id
        """, (recipe_id,))
        
        recipe = cursor.fetchone()
        
        if not recipe:
            conn.close()
            return error_response(404, '菜品不存在')
        
        if user_id:
            cursor.execute("""
                SELECT id FROM recipe_likes
                WHERE user_id = ? AND recipe_id = ?
            """, (user_id, recipe_id))
            recipe['is_liked'] = cursor.fetchone() is not None
            
            cursor.execute("""
                SELECT rating FROM recipe_ratings
                WHERE user_id = ? AND recipe_id = ?
            """, (user_id, recipe_id))
            rating = cursor.fetchone()
            recipe['user_rating'] = rating['rating'] if rating else None
        else:
            recipe['is_liked'] = False
            recipe['user_rating'] = None
        
        conn.close()
        
        return success_response(recipe, '获取菜品详情成功')
        
    except Exception as e:
        logger.error(f"获取菜品详情失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/recipes/<int:recipe_id>/like', methods=['POST'])
def like_recipe(recipe_id):
    """点赞/取消点赞菜品"""
    try:
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return error_response(401, '未授权')
        
        payload = decode_token(token[7:])
        if not payload:
            return error_response(401, '无效的token')
        
        user_id = payload['user_id']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id FROM recipes WHERE id = ?
        """, (recipe_id,))
        
        if not cursor.fetchone():
            conn.close()
            return error_response(404, '菜品不存在')
        
        cursor.execute("""
            SELECT id FROM recipe_likes
            WHERE user_id = ? AND recipe_id = ?
        """, (user_id, recipe_id))
        
        existing_like = cursor.fetchone()
        
        if existing_like:
            cursor.execute("""
                DELETE FROM recipe_likes
                WHERE user_id = ? AND recipe_id = ?
            """, (user_id, recipe_id))
            conn.commit()
            conn.close()
            return success_response({'is_liked': False}, '取消点赞成功')
        else:
            cursor.execute("""
                INSERT INTO recipe_likes (user_id, recipe_id)
                VALUES (?, ?)
            """, (user_id, recipe_id))
            conn.commit()
            conn.close()
            return success_response({'is_liked': True}, '点赞成功')
        
    except Exception as e:
        logger.error(f"点赞操作失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/recipes/<int:recipe_id>/rate', methods=['POST'])
def rate_recipe(recipe_id):
    """评分菜品"""
    try:
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return error_response(401, '未授权')
        
        payload = decode_token(token[7:])
        if not payload:
            return error_response(401, '无效的token')
        
        user_id = payload['user_id']
        data = request.get_json()
        
        is_valid, error_msg = validate_required_fields(data, ['rating'])
        if not is_valid:
            return error_response(400, error_msg)
        
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not (1 <= rating <= 5):
            return error_response(400, '评分必须在1-5之间')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id FROM recipes WHERE id = ?
        """, (recipe_id,))
        
        if not cursor.fetchone():
            conn.close()
            return error_response(404, '菜品不存在')
        
        cursor.execute("""
            SELECT id FROM recipe_ratings
            WHERE user_id = ? AND recipe_id = ?
        """, (user_id, recipe_id))
        
        existing_rating = cursor.fetchone()
        
        if existing_rating:
            cursor.execute("""
                UPDATE recipe_ratings
                SET rating = ?, comment = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND recipe_id = ?
            """, (rating, comment, user_id, recipe_id))
        else:
            cursor.execute("""
                INSERT INTO recipe_ratings (user_id, recipe_id, rating, comment)
                VALUES (?, ?, ?, ?)
            """, (user_id, recipe_id, rating, comment))
        
        conn.commit()
        conn.close()
        
        return success_response({'rating': rating, 'comment': comment}, '评分成功')
        
    except Exception as e:
        logger.error(f"评分操作失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/recipes/<int:recipe_id>/comments', methods=['GET'])
def get_recipe_comments(recipe_id):
    """获取菜品评论列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        offset = (page - 1) * page_size
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT rc.id, rc.content, rc.created_at,
                   u.id as user_id, u.name as user_name, u.avatar as user_avatar,
                   COUNT(DISTINCT rcl.id) as like_count
            FROM recipe_comments rc
            JOIN users u ON rc.user_id = u.id
            LEFT JOIN recipe_comment_likes rcl ON rc.id = rcl.comment_id
            WHERE rc.recipe_id = ? AND rc.parent_id IS NULL
            GROUP BY rc.id
            ORDER BY rc.created_at DESC
            LIMIT ? OFFSET ?
        """, (recipe_id, page_size, offset))
        
        comments = cursor.fetchall()
        
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM recipe_comments
            WHERE recipe_id = ? AND parent_id IS NULL
        """, (recipe_id,))
        
        total = cursor.fetchone()['total']
        
        conn.close()
        
        return success_response({
            'comments': comments,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        }, '获取评论列表成功')
        
    except Exception as e:
        logger.error(f"获取评论列表失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/recipes/<int:recipe_id>/comments', methods=['POST'])
def create_recipe_comment(recipe_id):
    """创建菜品评论"""
    try:
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return error_response(401, '未授权')
        
        payload = decode_token(token[7:])
        if not payload:
            return error_response(401, '无效的token')
        
        user_id = payload['user_id']
        data = request.get_json()
        
        is_valid, error_msg = validate_required_fields(data, ['content'])
        if not is_valid:
            return error_response(400, error_msg)
        
        content = data.get('content')
        parent_id = data.get('parent_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id FROM recipes WHERE id = ?
        """, (recipe_id,))
        
        if not cursor.fetchone():
            conn.close()
            return error_response(404, '菜品不存在')
        
        cursor.execute("""
            INSERT INTO recipe_comments (user_id, recipe_id, parent_id, content)
            VALUES (?, ?, ?, ?)
        """, (user_id, recipe_id, parent_id, content))
        
        conn.commit()
        conn.close()
        
        return success_response({'comment_id': cursor.lastrowid}, '评论成功')
        
    except Exception as e:
        logger.error(f"创建评论失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/recipes/<int:recipe_id>/share', methods=['POST'])
def share_recipe(recipe_id):
    """分享菜品"""
    try:
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return error_response(401, '未授权')
        
        payload = decode_token(token[7:])
        if not payload:
            return error_response(401, '无效的token')
        
        user_id = payload['user_id']
        data = request.get_json()
        
        share_type = data.get('share_type', 'general')
        platform = data.get('platform')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id FROM recipes WHERE id = ?
        """, (recipe_id,))
        
        if not cursor.fetchone():
            conn.close()
            return error_response(404, '菜品不存在')
        
        cursor.execute("""
            INSERT INTO recipe_shares (user_id, recipe_id, share_type, platform)
            VALUES (?, ?, ?, ?)
        """, (user_id, recipe_id, share_type, platform))
        
        conn.commit()
        conn.close()
        
        return success_response({'share_id': cursor.lastrowid}, '分享成功')
        
    except Exception as e:
        logger.error(f"分享操作失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/personalized', methods=['GET'])
def get_personalized_recommendations():
    """获取个性化推荐"""
    try:
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return error_response(401, '未授权')
        
        payload = decode_token(token[7:])
        if not payload:
            return error_response(401, '无效的token')
        
        user_id = payload['user_id']
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT r.id, r.name, r.image, r.description, r.cuisine,
                   r.cooking_time, r.difficulty, r.calories,
                   COALESCE(AVG(rr.rating), 0) as avg_rating,
                   COUNT(DISTINCT rl.id) as like_count,
                   COUNT(DISTINCT rc.id) as comment_count,
                    (
                        COALESCE(AVG(rr.rating), 0) * 0.4 +
                        COUNT(DISTINCT rl.id) * 0.3 +
                        COUNT(DISTINCT rc.id) * 0.3
                    ) as recommendation_score
            FROM recipes r
            LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
            LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
            LEFT JOIN recipe_comments rc ON r.id = rc.recipe_id
            GROUP BY r.id
            ORDER BY recommendation_score DESC
            LIMIT ?
        """, (limit,))
        
        recipes = cursor.fetchall()
        
        conn.close()
        
        return success_response(recipes, '获取个性化推荐成功')
        
    except Exception as e:
        logger.error(f"获取个性化推荐失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')


@recipe_recommendation_bp.route('/update-lists', methods=['POST'])
def update_recommendation_lists():
    """更新推荐榜单（定时任务）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, type FROM recommendation_lists WHERE is_active = 1")
        lists = cursor.fetchall()
        
        for list_item in lists:
            list_id = list_item['id']
            list_type = list_item['type']
            
            if list_type == 'hot':
                query = """
                    SELECT r.id,
                        COALESCE(AVG(rr.rating), 0) * 0.4 +
                        COUNT(DISTINCT rl.id) * 0.3 +
                        COUNT(DISTINCT rc.id) * 0.3 as score
                    FROM recipes r
                    LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
                    LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
                    LEFT JOIN recipe_comments rc ON r.id = rc.recipe_id
                    GROUP BY r.id
                    ORDER BY score DESC
                    LIMIT 10
                """
            elif list_type == 'quick':
                query = """
                    SELECT r.id,
                        (60 - r.cooking_time) * 0.5 +
                        COALESCE(AVG(rr.rating), 0) * 0.3 +
                        COUNT(DISTINCT rl.id) * 0.2 as score
                    FROM recipes r
                    LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
                    LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
                    WHERE r.cooking_time <= 30
                    GROUP BY r.id
                    ORDER BY score DESC
                    LIMIT 10
                """
            elif list_type == 'beginner':
                query = """
                    SELECT r.id,
                        CASE WHEN r.difficulty = '简单 THEN 1 ELSE 0 END * 0.5 +
                        COALESCE(AVG(rr.rating), 0') * 0.3 +
                        COUNT(DISTINCT rl.id') * 0.2 as score
                    FROM recipes r
                    LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
                    LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
                    GROUP BY r.id
                    ORDER BY score DESC
                    LIMIT 10
                """
            elif list_type == 'nutritious':
                query = """
                    SELECT r.id,
                        (r.calories BETWEEN 200 AND 500) * 0.4 +
                        COALESCE(AVG(rr.rating), 0) * 0.3 +
                        COUNT(DISTINCT rl.id) * 0.3 as score
                    FROM recipes r
                    LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
                    LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
                    GROUP BY r.id
                    ORDER BY score DESC
                    LIMIT 10
                """
            elif list_type == 'economical':
                query = """
                    SELECT r.id,
                        (r.calories <= 300) * 0.5 +
                        COALESCE(AVG(rr.rating), 0) * 0.3 +
                        COUNT(DISTINCT rl.id) * 0.2 as score
                    FROM recipes r
                    LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
                    LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
                    WHERE r.calories <= 400
                    GROUP BY r.id
                    ORDER BY score DESC
                    LIMIT 10
                """
            else:
                query = """
                    SELECT r.id,
                        COALESCE(AVG(rr.rating), 0) * 0.5 +
                        COUNT(DISTINCT rl.id) * 0.3 +
                        COUNT(DISTINCT rc.id) * 0.2 as score
                    FROM recipes r
                    LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
                    LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id
                    LEFT JOIN recipe_comments rc ON r.id = rc.recipe_id
                    GROUP BY r.id
                    ORDER BY score DESC
                    LIMIT 10
                """
            
            cursor.execute(query)
            recipes = cursor.fetchall()
            
            cursor.execute("DELETE FROM list_recipes WHERE list_id = ?", (list_id,))
            
            for rank, recipe in enumerate(recipes, 1):
                cursor.execute("""
                    INSERT INTO list_recipes (list_id, recipe_id, rank_position, score)
                    VALUES (?, ?, ?, ?)
                """, (list_id, recipe['id'], rank, recipe['score']))
        
        conn.commit()
        conn.close()
        
        return success_response({'message': '榜单更新成功'}, '榜单更新成功')
        
    except Exception as e:
        logger.error(f"更新榜单失败: {str(e)}")
        return error_response(500, f'服务器错误 {str(e)}')
