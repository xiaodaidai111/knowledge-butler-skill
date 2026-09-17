import base64
import json
import logging

from flask import Blueprint, request

from services.health_score import HealthScoreCalculator
from utils import decode_token, error_response, get_db_connection, success_response

logger = logging.getLogger(__name__)

takeaway_health_bp = Blueprint('takeaway_health', __name__)

PARAM_KEYS = [
    'food_text',
    'ingredients',
    'portion_grams',
    'cooking_method',
    'delivery_time',
    'safe_time',
    'decay_lambda',
    'packaging_material',
    'food_temperature',
    'user_goals',
]


def _extract_user_id():
    auth = request.headers.get('Authorization', '')
    if not auth:
        return None

    token = auth[7:] if auth.startswith('Bearer ') else auth
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get('user_id')


def _merge_params(data):
    params = dict(data.get('params') or {})
    for key in PARAM_KEYS:
        if key in data and key not in params:
            params[key] = data.get(key)
    return params


def _get_nutrition_items(result):
    analysis = result.get('nutrition_analysis', {})
    items = []
    for nutrient, info in analysis.items():
        unit = 'kcal' if nutrient == 'calories' else ('mg' if nutrient == 'sodium' else 'g')
        items.append({
            'key': nutrient,
            'name': _get_nutrient_name(nutrient),
            'value': info.get('value', 0),
            'recommended': info.get('recommended', 0),
            'ratio': info.get('ratio', 0),
            'status': _map_status(info.get('status', 'ok')),
            'unit': unit,
        })
    return items


def _save_analysis(user_id, result):
    if not user_id:
        return

    try:
        nutrition = result.get('nutrition_analysis', {})
        dimensions = {
            'base': result.get('model', {}).get('h_base', 0),
            'temp': result.get('model', {}).get('c_temp', 1),
            'pack': result.get('model', {}).get('c_pack', 1),
            'personal': result.get('model', {}).get('h_personal', 0),
        }

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO takeaway_analysis (
                        user_id, name, score, calories, protein, fat, carbs,
                        dimensions, suggestions, analysis_text
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        result.get('name', '外卖评估'),
                        result.get('score', 0),
                        nutrition.get('calories', {}).get('value', 0),
                        nutrition.get('protein', {}).get('value', 0),
                        nutrition.get('fat', {}).get('value', 0),
                        nutrition.get('carbs', {}).get('value', 0),
                        json.dumps(dimensions, ensure_ascii=False),
                        json.dumps(result.get('suggestions', []), ensure_ascii=False),
                        f"{result.get('name', '该餐品')}的健康评分为{result.get('score', 0)}分",
                    ),
                )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning('保存外卖分析记录失败: %s', exc)


def _history_rows(user_id):
    if not user_id:
        return []

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT name, score, created_at
                    FROM takeaway_analysis
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 20
                    """,
                    (user_id,),
                )
                return cursor.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.warning('读取外卖分析历史失败: %s', exc)
        return []


@takeaway_health_bp.route('/api/takeaway/health/analyze/text', methods=['POST'])
def analyze_takeaway_text():
    data = request.get_json(silent=True) or {}
    food_text = (data.get('food_text') or '').strip()
    if not food_text:
        return error_response(400, '请输入菜品名称或外卖描述')

    params = _merge_params(data)

    try:
        result = HealthScoreCalculator.analyze_food_from_text(food_text, params)
        _save_analysis(_extract_user_id(), result)
        return success_response(_build_response(result), '分析成功')
    except Exception as exc:  # noqa: BLE001
        logger.exception('分析外卖文本失败')
        return error_response(500, f'分析失败：{exc}')


@takeaway_health_bp.route('/api/takeaway/health/analyze/image', methods=['POST'])
def analyze_takeaway_image():
    try:
        image_bytes = None
        
        # 支持 multipart/form-data 文件上传
        if 'image_data' in request.files:
            image_file = request.files['image_data']
            image_bytes = image_file.read()
        else:
            # 支持 JSON base64 数据
            data = request.get_json(silent=True) or {}
            image_data = data.get('image_data', '')
            if not image_data:
                return error_response(400, '请先上传外卖图片')
            
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            image_bytes = base64.b64decode(image_data)
        
        params = _merge_params(request.get_json(silent=True) or {})
        
        result = HealthScoreCalculator.analyze_food_from_image(image_bytes, params)
        _save_analysis(_extract_user_id(), result)
        return success_response(_build_response(result), '分析成功')
    except Exception as exc:  # noqa: BLE001
        logger.exception('分析外卖图片失败')
        return error_response(500, f'分析失败：{exc}')


@takeaway_health_bp.route('/api/takeaway/health/history', methods=['GET'])
def get_takeaway_history():
    user_id = _extract_user_id()
    rows = _history_rows(user_id)
    history = [
        {
            'name': row.get('name', '外卖评估'),
            'score': row.get('score', 0),
            'created_at': row.get('created_at').isoformat() if row.get('created_at') else '',
        }
        for row in rows
    ]
    return success_response(history, '获取历史成功')


def _build_response(result):
    model = result.get('model', {})
    return {
        'name': result.get('name', '外卖评估'),
        'score': int(result.get('score', 0)),
        'nutrition': _get_nutrition_items(result),
        'suggestions': result.get('suggestions', []),
        'ingredients': result.get('ingredients', []),
        'processing': result.get('processing', 'unknown'),
        'estimated_nutrition': result.get('estimated_nutrition', {}),
        'model': model,
        'params': result.get('params', {}),
        'dimensions': [
            {'key': 'base', 'name': '基础健康分', 'score': int(round(model.get('h_base', 0) * 100))},
            {'key': 'temp', 'name': '时效温控', 'score': int(round(model.get('c_temp', 1) * 100))},
            {'key': 'pack', 'name': '包装安全', 'score': int(round(model.get('c_pack', 1) * 100))},
            {'key': 'personal', 'name': '个性化适配', 'score': int(round(model.get('h_personal', 0) * 100))},
        ],
    }


def _get_nutrient_name(key):
    mapping = {
        'calories': '热量',
        'protein': '蛋白质',
        'fat': '脂肪',
        'saturated_fat': '饱和脂肪',
        'carbs': '碳水',
        'sugar': '糖',
        'sodium': '钠',
        'fiber': '膳食纤维',
    }
    return mapping.get(key, key)


def _map_status(status):
    mapping = {
        'low': '偏低',
        'ok': '适中',
        'high': '偏高',
    }
    return mapping.get(status, '适中')
